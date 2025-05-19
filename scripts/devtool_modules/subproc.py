'''
Subprocess utilities for devtool.

This module provides a set of functions for running subprocesses
and handling their output. It includes functions for running
subprocesses with or without a shell, capturing their output,
and handling errors. The functions are designed to be used in
the context of a command line interface (CLI).
'''

from contextlib import suppress
from shutil import which
from typing import Any, TYPE_CHECKING
from pathlib import Path
import os
import subprocess

import psutil
if TYPE_CHECKING:
    from subprocess import _FILE

from devtool_modules.utils import DEBUG
from devtool_modules.paths import PROJECT_ROOT

def run(*cmds: Any,
        cwd: os.PathLike|str=PROJECT_ROOT,
        env: dict[str,str]|None=None,
        shell: bool=False,
        stdout: '_FILE'=None,
        stderr: '_FILE'=None,
    ) -> subprocess.CompletedProcess:
    "Run the given command."
    cmd = [str(arg) for arg in cmds]
    cmd[0] = which(cmd[0]) or cmd[0]
    DEBUG(f"Running command: {' '.join(cmd)}")
    env = env or os.environ.copy()
    cwd = cwd or Path.cwd()
    result: subprocess.CompletedProcess = subprocess.run(cmd,
                                                        cwd=str(cwd),
                                                        env=env,
                                                        shell=shell,
                                                        stderr=stderr,
                                                        stdout=stdout,
                                                        )
    if result.returncode != 0:
        raise RuntimeError(f"Command exited with return code {result.returncode}.")
    DEBUG("Command completed successfully.")
    return result

def capture(*cmds: Any,
            env: dict[str,str]|None=None,
            shell: bool=False,
        stdout: '_FILE'=None,
        stderr: '_FILE'=None,
            **kwargs) -> str:
    "Capture the output of the given command."
    cmd = [str(arg) for arg in cmds]
    cmd[0] = which(cmd[0]) or cmd[0]
    env = env or os.environ.copy()
    DEBUG(f"Running command: {' '.join(cmd)}")
    result: subprocess.CompletedProcess = subprocess.run(cmd,
                                                        cwd=str(PROJECT_ROOT),
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
            cwd: os.PathLike|str=PROJECT_ROOT,
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
    DEBUG(f"Running command: {' '.join(cmd)}")
    proc = subprocess.Popen(cmd,
                            cwd=str(cwd),
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
