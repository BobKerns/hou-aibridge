"""
Modules for the zabob command-line utility.
"""

from typing import Final
import json
from contextlib import suppress

from zabob.utils import (
    Level,
    LEVELS,
    DEBUG,
    VERBOSE,
    INFO,
    QUIET,
    SILENT,
)
from zabob.paths import (
    ZABOB_MODULES_DIR,
    ZABOB_ROOT,
    ZABOB_PACKAGE_FILE,
    ZABOB_DOCKER_DIR,
    ZABOB_HOUDINI_20_5_DIR,
    HOUDINI_PROJECTS,
    ZABOB_DOCS_DIR,
    ZABOB_IMAGES_DIR,
    ZABOB_BIN_DIR,
    ZABOB_NODE_BIN,
    ZABOB_MARKSERV,
    ZABOB_PKG_DIR,
    SUBPROJECTS,
    ZABOB_DEFAULT_CREDENTIALS,
    ZABOB_DEFAULT_COMPOSE,
    ZABOB_BROWSE_PORT_FILE,
    ZABOB_BROWSE_RELOAD_FILE,
    ZABOB_BROWSE_PID_FILE,
    ZABOB_BROWSE_LOG_FILE,
)
from zabob.subproc import (
    run,
    capture,
    spawn,
    check_pid,
)
from zabob.main import main
from zabob.update import update
from zabob.setup import setup
from zabob.server import server
from zabob.node import node_group
from zabob.houdini import houdini_commands
from zabob.houdini_versions import cli as houdini_cli

def version():
    with suppress(ImportError):
        # This will fail unless we build it as a package first.
        from importlib.metadata import version as get_version
        return get_version("zabob")
    try:
        with open(ZABOB_PACKAGE_FILE, "r", encoding="utf-8") as f:
            package_data = json.load(f)
            return package_data.get("version", "0.0.0")
    except FileNotFoundError:
        default: Final[str] = "0.0.0"
        print(f"Warning: {ZABOB_PACKAGE_FILE} not found. Using default version {default}.")
        return default


__version__: Final[str] = version()
"""
Version of the zabob-modules package.
This is the version of the package as specified in the package.json file.
"""

__all__: Final[tuple[str, ...]] = (
    "ZABOB_MODULES_DIR",
    "ZABOB_ROOT",
    "ZABOB_PACKAGE_FILE",
    "ZABOB_DOCKER_DIR",
    "ZABOB_HOUDINI_20_5_DIR",
    "HOUDINI_PROJECTS",
    "ZABOB_DOCS_DIR",
    "ZABOB_IMAGES_DIR",
    "ZABOB_BIN_DIR",
    "ZABOB_NODE_BIN",
    "ZABOB_MARKSERV",
    "ZABOB_PKG_DIR",
    "SUBPROJECTS",
    "ZABOB_DEFAULT_CREDENTIALS",
    "ZABOB_DEFAULT_COMPOSE",
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
    "ZABOB_BROWSE_PORT_FILE",
    "ZABOB_BROWSE_RELOAD_FILE",
    "ZABOB_BROWSE_PID_FILE",
    "ZABOB_BROWSE_LOG_FILE",
    'update', 'server', 'node_group', 'main', 'setup', 'houdini_commands', 'houdini_cli',
)
