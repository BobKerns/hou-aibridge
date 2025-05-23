'''
Server subcommands of the devtool utility.
'''

from contextlib import suppress
from os import PathLike
import socket
import subprocess
import sys
from typing import Final, NamedTuple
from time import sleep

import psutil

from devtools.paths import (
    LOG_FILE, MARKSERV, PID_FILE, PORT_FILE, PROJECT_ROOT, RELOAD_FILE,
)
from devtools.utils import DEBUG
from devtools.subproc import check_pid, spawn
from devtools.main import main


@main.group(name='server')
def server() -> None:
    """
    <CMD> Operations on the local documentation server.
    Use the --help option for more information on a specific command.
    """
    pass


def find_free_port():
    """Finds an available port on the system.

    Returns:
        int: An available port number.
    """
    sock = socket.socket()
    # We are binding on all interfaces, to find a port that is completely free.
    # We do not communicate with the socket, and immediately discard it, and
    # we never listen on it, so we do not need to worry about it being an exposed
    # interface.
    #
    # We also want to avoid creating a situation where we get a port that is in
    # the process of being opened by another process, but not yet bound. We are
    # not in charge of the eventual binding and listen; we cannot just bind to
    # one interface. We would have to predict and enumerate the interfaces that the
    # server will bind to, and then bind to all of them, which is not reliably
    # possible.
    #
    # Race conditions here are unavoidable, but this should be a good enough
    # approximation. We pass the port off to the server, which will then bind to it
    # with localhost, so it will be bound to the correct interface, and we can't do
    # anything about the race condition. The user can retry if they get an error.
    sock.bind(('', 0))  # Bind to all interfaces on a random available port
    port = sock.getsockname()[1]
    sock.close()
    return port

def check_port(port: int|None):
    """Check if a port is in use on the system.

    Args:
        port (int): The port number to check.

    Returns:
        bool: True if the port is in use (a connection can be established), False otherwise.
    """
    if port is None or port <= 0:
        return False
    def try_AF(af: int):
        with suppress(Exception):
            sock = socket.socket(af, socket.SOCK_STREAM)
            sock.settimeout(1)  # Set a timeout value (in seconds)
            sock.connect(("localhost", port))
            sock.close()
            return True
        return False
    return try_AF(socket.AF_INET6) or try_AF(socket.AF_INET)


def read_id_file(file: PathLike|str) -> int | None:
    "Read the id from the given file."
    file = PROJECT_ROOT / file
    with suppress(Exception):
        if not file.exists():
            return None
        with file.open('r') as f:
            return int(f.read().strip())
    return None

def save_id_file(file: PathLike|str, value: int|None) -> None:
    "Save the id to the given file."
    file = PROJECT_ROOT / file
    if value is None or value <= 0:
        value = 0
    with file.open('w') as f:
        f.write(str(value))

class ServerStatus(NamedTuple):
    """
    A named tuple representing the status of the server.
    The first value is a boolean indicating if the server is running.
    The second value is a tuple containing the pid, html port, and reload port.
    The pid will be None if the server is not running.
    The html port and reload port will be None if they are not set, otherwise
    they will be the port numbers of the last run. This means we will try to
    reuse the same ports if the server is restarted.
    """
    pid: int | None
    "Will be None if the server is not running."
    html_port: int | None
    "Will be None if the server has not been started."
    reload_port: int | None
    "Will be None if the server has not been started."


def get_server_status() -> ServerStatus:
    '''
    Check the status of the server. Cleans up dead servers and pid/port files
    if they are found, and returns the status of the server.

    Returns:
        ServerStatus: A named tuple containing the status of the server.
    '''
    html_port = read_id_file(PORT_FILE)
    reload_port = read_id_file(RELOAD_FILE)
    pid = read_id_file(PID_FILE)
    html_port_ok = check_port(html_port)
    reload_port_ok = check_port(reload_port)
    pid_ok = check_pid(pid)
    DEBUG(f'{html_port=} {html_port_ok=}')
    DEBUG(f'{reload_port=} {reload_port_ok=}')
    DEBUG(f'{pid=} {pid_ok=}')
    DEBUG(f'{check_port(html_port)=} {check_port(reload_port)=} {check_pid(pid)=}')
    status = html_port_ok and reload_port_ok and pid_ok
    if not status:
        stop_server(pid)
        return ServerStatus(None, html_port, reload_port)
    return ServerStatus(pid, html_port, reload_port)


@server.command(name='status')
def server_status(silent: bool=False) -> None:
    "Check the status of the server."
    pid, html_port, reload_port = get_server_status()
    if not silent:
        if pid is not None:
            print(f"Server is running, {pid=}, {html_port=}, {reload_port=}")
            print(f"Server is running on http://localhost:{html_port}")
        else:
            print("Server is not running.")
            print(f'Last used ports: {html_port=} {reload_port=}')
    if pid is None:
        sys.exit(1)

def stop_server(pid: int|None) -> None:
    """
    Stop the server if it is running.

    Args:
        pid (int|None): The process ID of the server.
    """
    if pid is not None and check_pid(pid):
        with suppress(Exception):
            p = psutil.Process(pid)
            p.terminate()
        # If the server is not running, we clear the pid file. We leave it in place because
        # it is the key for the VSCode Explorer's collapsing related files together, so it
        # declutters the explorer view. We keep the port files in place so that we can
        # reuse the ports if the server is restarted, allowing stale browser tabs to reconnect.
        save_id_file(PID_FILE, 0)


@server.command(name='stop')
def stop_server_command() -> None:
    "Stop the server if it is running."
    pid = read_id_file(PID_FILE)
    stop_server(pid)
    print("Server killed.")


def start_server() -> ServerStatus:
    """
    Start the server if it is not running.

    Returns:
        ServerStatus: A named tuple containing the status of the server.
    """
    (pid, html_port, reload_port) = get_server_status()
    if pid is not None:
        DEBUG("Server is already running.")
        return ServerStatus(pid, html_port, reload_port)
    if not html_port:
        html_port = find_free_port()
    if not reload_port:
        reload_port = find_free_port()
    save_id_file(PORT_FILE, html_port)
    save_id_file(RELOAD_FILE, reload_port)
    if DEBUG.enabled:
        DEBUG(f"Starting server on port {html_port} with reload port {reload_port}.")
        silent_flag = ()
        output_flags = {'stderr': subprocess.PIPE}
    else:
        silent_flag = ('--silent',)
        # Open a stream to the log file. We don't close it as we pass ownership to the spawned
        # process. We don't want to close it, as the process will be writing to it.
        logstream = open(LOG_FILE, 'w')

        output_flags = {'stdout': logstream, 'stderr': logstream}
    proc: subprocess.Popen = spawn(MARKSERV,
        '-p', str(html_port),
        '-b', str(reload_port),
        '--browser', 'false',
        *silent_flag,
        'README.md',
        **output_flags       # type: ignore[arg-type]
        )
    if proc.returncode:
        error_message = proc.stderr.read().decode() if proc.stderr else "Unknown error"
        print(f"Failed to start the server: {error_message}", file=sys.stderr)
        sys.exit(proc.returncode)
    pid = proc.pid
    if not pid:
        print("Failed to get the process ID.", file=sys.stderr)
        save_id_file(PID_FILE, 0)
        return ServerStatus(None, html_port, reload_port)
    save_id_file(PID_FILE, pid)
    for i in range(10):
        if check_port(html_port):
            break
        DEBUG(f"Waiting for server to start on port {html_port}...")
        if i == 9:
            print(f"Server failed to start on port {html_port}.", file=sys.stderr)
            sys.exit(1)
        # We don't want to block the server from starting, so we just wait a bit.
        sleep(0.1 * (i + 1))
    return ServerStatus(pid, html_port, reload_port)

@server.command(name='start')
def start_server_command() -> None:
    "Start the server if it is not running."
    pid, html_port, reload_port = get_server_status()
    if pid is not None:
        print(f"Server is running on http://localhost:{html_port}")
        sys.exit(0)
    status = start_server()
    if status.pid is not None:
        print(f"Server started on http://localhost:{status.html_port}")
    else:
        print("Failed to start the server.", file=sys.stderr)
        sys.exit(1)

__all__: Final[tuple[str, ...]] = (
    'server',
    'start_server',
    'stop_server',
    'get_server_status',
    'check_port',
    'find_free_port',
    'read_id_file',
    'save_id_file',
)
