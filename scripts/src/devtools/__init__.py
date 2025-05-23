"""
Modules for the devtool command-line utility.
"""

from typing import Final
import json
from contextlib import suppress

from devtools.utils import (
    Level,
    LEVELS,
    DEBUG,
    VERBOSE,
    INFO,
    QUIET,
    SILENT,
)
from devtools.paths import (
    SCRIPTS_DIR,
    PROJECT_ROOT,
    PACKAGE_PATH,
    DOCKER_DIR,
    HOUDINI_20_5_DIR,
    HOUDINI_PROJECTS,
    DOCS_DIR,
    IMAGES_DIR,
    BIN_DIR,
    NODE_BIN,
    MARKSERV,
    DEVTOOL_DIR,
    SUBPROJECTS,
    DEFAULT_CREDENTIALS,
    DEFAULT_COMPOSE,
    PORT_FILE,
    RELOAD_FILE,
    PID_FILE,
    LOG_FILE,
)
from devtools.subproc import (
    run,
    capture,
    spawn,
    check_pid,
)
from devtools.main import main
from devtools.update import update
from devtools.setup import setup
from devtools.server import server
from devtools.node import node_group
from devtools.houdini import houdini_commands
from devtools.houdini_versions import cli as houdini_cli

def version():
    with suppress(ImportError):
        # This will fail unless we build it as a package first.
        from importlib.metadata import version as get_version
        return get_version("devtools")
    try:
        with open(PACKAGE_PATH, "r", encoding="utf-8") as f:
            package_data = json.load(f)
            return package_data.get("version", "0.0.0")
    except FileNotFoundError:
        default: Final[str] = "0.0.0"
        print(f"Warning: {PACKAGE_PATH} not found. Using default version {default}.")
        return default


__version__: Final[str] = version()
"""
Version of the devtool package.
This is the version of the package as specified in the package.json file.
"""

__all__: Final[tuple[str, ...]] = (
    "SCRIPTS_DIR",
    "PROJECT_ROOT",
    "PACKAGE_PATH",
    "DOCKER_DIR",
    "HOUDINI_20_5_DIR",
    "HOUDINI_PROJECTS",
    "DOCS_DIR",
    "IMAGES_DIR",
    "BIN_DIR",
    "NODE_BIN",
    "MARKSERV",
    "DEVTOOL_DIR",
    "SUBPROJECTS",
    "DEFAULT_CREDENTIALS",
    "DEFAULT_COMPOSE",
    "main",
    "Level",
    "LEVELS",
    'run',
    'capture',
    'spawn',
    'check_pid',
    "DEBUG",
    "VERBOSE",
    "INFO",
    "QUIET",
    "SILENT",
    "__version__",
    "PORT_FILE",
    "RELOAD_FILE",
    "PID_FILE",
    "LOG_FILE",
    'update', 'server', 'node_group', 'main', 'setup', 'houdini_commands', 'houdini_cli',
)
