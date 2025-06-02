'''
Subprocess utilities for zabob-modules.

This module provides a set of functions for running subprocesses
and handling their output. It includes functions for running
subprocesses with or without a shell, capturing their output,
and handling errors. The functions are designed to be used in
the context of a command line interface (CLI).
'''

from collections.abc import Sequence
from contextlib import suppress
from shutil import which
from typing import Any, TYPE_CHECKING, Never
from pathlib import Path
import os
import subprocess
# For re-export for consistency
from subprocess import CompletedProcess

import psutil
if TYPE_CHECKING:
    from subprocess import _FILE

from zabob.common.common_utils import DEBUG

def debug_cmd(cmd: Sequence[str],
              cwd: os.PathLike|str|None=None,
               env: dict[str,str]|None=None) -> None:
    """
    Print the current working directory and environment variables for debugging.
    Args:
        cwd (os.PathLike|str|None): The current working directory.
        env (dict[str,str]|None): The environment variables.
    """
    if DEBUG.enabled:
        cwd = Path(cwd or Path.cwd())
        DEBUG(f"Current working directory: {cwd}")
        if env is not None:
            for key, value in env.items():
                DEBUG(f"Env:  {key}={value}")
        DEBUG(f"Command: {' '.join(cmd)}")

def run(*cmds: Any,
        cwd: os.PathLike|str|None=None,
        env: dict[str,str]|None=None,
        shell: bool=False,
        stdout: '_FILE'=None,
        stderr: '_FILE'=None,
        dry_run: bool=False,
    ) -> subprocess.CompletedProcess:
    "Run the given command."
    cmd = [str(arg) for arg in cmds]
    cmd[0] = which(cmd[0]) or cmd[0]
    cwd = Path(cwd or Path.cwd())
    DEBUG(f"{cwd.name}> {' '.join(cmd)}")
    debug_cmd(cmd, cwd, env)
    if dry_run:
        return subprocess.CompletedProcess(cmd, 0)
    env = env or os.environ.copy()
    result: subprocess.CompletedProcess = subprocess.run(cmd,
                                                        cwd=str(cwd) if cwd is not None else None,
                                                        env=env,
                                                        shell=shell,
                                                        stderr=stderr,
                                                        stdout=stdout,
                                                        )
    if result.returncode != 0:
        raise RuntimeError(f"Command exited with return code {result.returncode}.")
    DEBUG("Command completed successfully.")
    return result

def exec_cmd(*cmds: Any,
        cwd: os.PathLike|str|None=None,
        env: dict[str,str]|None=None,
        shell: bool=False,
        stdout: '_FILE'=None,
        stderr: '_FILE'=None,
    ) -> Never:
    "Run the given command, replacing this process."
    cmd = [str(arg) for arg in cmds]
    cmd[0] = which(cmd[0]) or cmd[0]
    cwd = Path(cwd or Path.cwd())
    DEBUG(f"{cwd.name}> {' '.join(cmd)}")
    debug_cmd(cmd, cwd, env)
    env = env or os.environ.copy()
    if shell:
        DEBUG("Running command in shell mode.")
    else:
        DEBUG("Running command in non-shell mode.")
    os.execve(cmd[0], cmd, env)  #

def capture(*cmds: Any,
            env: dict[str,str]|None=None,
            shell: bool=False,
            stdout: '_FILE'=None,
            stderr: '_FILE'=None,
            cwd: os.PathLike|str|None=None,
            **kwargs) -> str:
    "Capture the output of the given command."
    cmd = [str(arg) for arg in cmds]
    cmd[0] = which(cmd[0]) or cmd[0]
    env = env or os.environ.copy()
    debug_cmd(cmd, cwd, env)
    result: subprocess.CompletedProcess = subprocess.run(cmd,
                                                        cwd=str(cwd) if cwd is not None else None,
                                                        capture_output=True,
                                                        text=True,
                                                        env=env,
                                                        shell=shell,
                                                        stdout=stdout,
                                                        stderr=stderr,
                                                        **kwargs
                                                        )
    if result.returncode != 0:
        raise RuntimeError(f"Command exited with return code {result.returncode}.")
    DEBUG("Command completed successfully.")
    text = result.stdout
    DEBUG(f"Command output: '{text}'")
    return text


def spawn(*cmds: Any,
            cwd: os.PathLike|str|None=None,
            env: dict[str,str]|None=None,
            shell: bool=False,
            stdout: '_FILE'=None,
            stderr: '_FILE'=None,
            **kwargs
        ) -> subprocess.Popen:
    "Spawn the given command."
    cmd = [str(arg) for arg in cmds]
    cmd[0] = which(cmd[0]) or cmd[0]
    env = env or os.environ.copy()
    debug_cmd(cmd, cwd, env)
    proc = subprocess.Popen(cmd,
                            cwd=str(cwd) if cwd is not None else None,
                            env=env,
                            shell=shell,
                            stdout=stdout,
                            stderr=stderr,
                            **kwargs
                            )
    # In the expected case, the process will not have terminated,
    # and the return code will be None. If the process has already terminated,
    # (whether with "success" or otherwise) we raise an error.
    if proc.returncode is not None:
        raise RuntimeError(f"Command exited prematurely with return code {proc.returncode}.")
    DEBUG("Command started successfully.")
    return proc


def check_pid(pid: int|None):
    """
    Check if a process with the given PID is running using psutil.
    Args:
        pid (int|None): The process ID to check.
    Returns:
        bool: True if the process is running, False otherwise.
    """
    if pid is None or pid <= 0:
        return False
    with suppress(Exception):
        return psutil.pid_exists(pid)
    return False

__all__ = (
    "run",
    "capture",
    "spawn",
    "check_pid",
    "exec_cmd",
    "CompletedProcess",
)
