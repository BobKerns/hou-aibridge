"""
Modules for the devtool command-line utility.
"""

from typing import Final
import json
from contextlib import suppress

from devtool_modules.utils import (
    Level,
    LEVELS,
    DEBUG,
    VERBOSE,
    INFO,
    QUIET,
    SILENT,
)
from devtool_modules.paths import (
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
from devtool_modules.subproc import (
    run,
    capture,
    spawn,
    check_pid,
)
from devtool_modules.main import main
from devtool_modules.update import update
from devtool_modules.setup import setup
from devtool_modules.server import server
from devtool_modules.node import node_group

def version():
    with suppress(ImportError):
        # This will fail unless we build it as a package first.
        from importlib.metadata import version as get_version
        return get_version("devtool")
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
    'update', 'server', 'node_group', 'main', 'setup',
)
