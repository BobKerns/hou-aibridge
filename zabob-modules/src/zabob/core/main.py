'''
Top level command line interface for the zabob package.
'''

from os import PathLike
from pathlib import Path
from shutil import which
import sys
import webbrowser
import click
import os

from zabob.core.paths import ZABOB＿MARKSERV, ZABOB_ROOT
from zabob.core.hython import hython
from zabob.common.common_utils import INFO, QUIET, SILENT, VERBOSE, Level, DEBUG
from zabob.common.subproc import run


@click.group()
@click.option('--debug', is_flag=True, help="Enable debug mode.")
@click.option('--verbose', is_flag=True, help="Enable verbose mode.")
@click.option('--quiet', is_flag=True,
              help="Suppress most output.")
@click.option('--silent', is_flag=True,
              help="Suppress all output.")
def main(debug: bool=False,
         verbose: bool=False,
         quiet: bool=False,
         silent: bool=False,
         ) -> None:
    """
    Update and generate documentation and other files, and perform
    other project-specific tasks.

    The most verbose output is produced in debug mode, followed by
    verbose mode, then quiet mode, and finally silent mode. The
    defalt is between verbose and quiet mode. Output will be as verbose
    as the most verbose flag set. For example, if debug and quiet are set,
    debug mode will be used, and no output will be suppressed.
    Supply the --help option for more information on a specific command.
    """
    if debug:
        Level.level = DEBUG
    elif verbose:
        Level.level = VERBOSE
    elif quiet:
        Level.level = QUIET
    elif silent:
        Level.level = SILENT
    else:
        Level.level = INFO
    if Level.level not in (INFO, SILENT):
        QUIET(f"Logging level set to {Level.level}.")


@main.command(name='sync')
def sync_dependencies() -> None:
    "Update the requirements.txt and uv.lock files."
    if DEBUG.enabled:
        for key, value in os.environ.items():
            DEBUG(f"{key}={value}")
    # run('uv', 'sync', env=os.environ.copy())
    shell('-c', 'uv sync')


@main.command(name='shell')
@click.argument('args', nargs=-1)
@click.option('--direnv', is_flag=True,
              help="Use direnv to set up the environment.")
@click.option('--shell', is_flag=False,
              help="Specify the shell to use instead of the value in the SHELL environment variable.")
def shell(args: list[str],
          direnv: bool=False,
          shell: str|None=None,
          ) -> None:
    """
    Open a shell in the current directory. By default, the shell will be
    the value of the SHELL environment variable.

    Arguments:
        args: The arguments to pass to the shell. If no arguments are
              provided, the shell will be opened with no arguments.
        direnv: If set, direnv will be used to set up the environment.
                This is useful if you have a .envrc file in the current
                directory.
        shell: The shell to use. If not set, the value of the SHELL
               environment variable will be used. This is useful if you
               want to use a different shell than the default.

    """
    shell = which(shell or os.getenv('SHELL', 'bash'))
    if shell is None:
        print("No shell found. Please install a shell.", file=sys.stderr)
        sys.exit(1)
    env = os.environ.copy()
    if not direnv:
        env['NO_DIRENV'] = '1'

    run(shell, '--', *args,
        cwd=Path.cwd(),
        env=env)


@main.command(name='browse')
@click.argument('file', type=click.Path(exists=True), default=ZABOB_ROOT / 'README.md')
def browse_docs(file: PathLike|str = ZABOB_ROOT / 'README.md') -> None:
    "[<PATH>] Open the documentation in a browser."

    from zabob.core.server import get_server_status, start_server

    file = Path(file).resolve()
    if not file.exists():
        print(f"File {file} not found, browsing directory.", file=sys.stderr)
        file = file.parent

    if ZABOB_ROOT not in file.parents and file != ZABOB_ROOT:
        # Onn general security principles, we should not allow
        # browsing outside the project directory. It's not really a
        # security issue here.
        print(f"File {file} is not in the project directory.", file=sys.stderr)
        sys.exit(1)

    file = file.relative_to(ZABOB_ROOT)

    if not ZABOB＿MARKSERV.exists():
        print(f"Markserv not found at {ZABOB＿MARKSERV}. Please run 'build setup' first.", file=sys.stderr)
        sys.exit(1)

    (pid, html_port, reload_port) = get_server_status()
    if pid is None:
        (pid, html_port, reload_port) = start_server()
    if not pid:
        print("Failed to start the server.", file=sys.stderr)
        sys.exit(1)
    assert html_port is not None
    VERBOSE(f"Opening documentation in browser at http://localhost:{html_port}/{file}")
    webbrowser.open(f'http://localhost:{html_port}/{file}')


__all__ = (
    "main", 'sync_dependencies', 'browse_docs',
)

if __name__ == "__main__":
    main()

