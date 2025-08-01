'''
Useful pathname constants.
'''

from pathlib import Path
from typing import Final
from collections.abc import Mapping
import os
import sys

from semver import Version

from zabob.common import (
    ZABOB_OUT_DIR as _ZABOB_OUT_DIR,
    ZABOB_ZCOMMON_DIR as _ZABOB_ZCOMMON_DIR,
    ZABOB_HOME_DIR as _ZABOB_HOME_DIR,
    ZABOB_HOUDINI_DATA as _ZABOB_HOUDINI_DATA,
)

# Shared constants
ZABOB_CORE_DIR: Final[Path] = Path(__file__).resolve().parent
_ZABOB_PKG_DIR: Final[Path] = ZABOB_CORE_DIR.parent
_ZABOB_SRC_DIR: Final[Path] = _ZABOB_PKG_DIR.parent
ZABOB_MODULES_DIR: Final[Path] = _ZABOB_SRC_DIR.parent
ZABOB_ROOT: Final[Path] = ZABOB_MODULES_DIR.parent
ZABOB_CHAT_DIR: Final[Path] = ZABOB_ROOT / "zabob-chat"
ZABOB_PACKAGE_FILE: Final[Path] = ZABOB_CHAT_DIR / "package.json"
ZABOB_ZCOMMON_DIR: Final[Path] = _ZABOB_ZCOMMON_DIR
ZABOB_HOME_DIR: Final[Path] = _ZABOB_HOME_DIR
ZABOB_HOUDINI_DATA: Final[Path] = _ZABOB_HOUDINI_DATA

ZABOB_CHECKSUMS: Final[Path] = ZABOB_ROOT / ".checksums"
'''
Checksums for the project files.
This is used to check if the project files have changed.
'''
ZABOB_OUT_DIR: Final[Path] = _ZABOB_OUT_DIR
'''
Output directory for the zabob project. This directory is used
to store generated files for development; it is excluded from
.git and should not be committed to the repository.
'''

# Add useful path constants
ZABOB_DOCKER_DIR: Final[Path] = ZABOB_ROOT / "docker"
ZABOB_HOUDINI_DIR: Final[Path] = ZABOB_ROOT / "houdini"
ZABOB_HOUDINI_20_5_DIR: Final[Path] = ZABOB_HOUDINI_DIR / "h20.5"
ZABOB_DOCS_DIR: Final[Path] = ZABOB_ROOT / "docs"
ZABOB_IMAGES_DIR: Final[Path] = ZABOB_DOCKER_DIR / "images"
ZABOB_DEFAULT_CREDENTIALS: Final[Path] = ZABOB_DOCKER_DIR / "sidefx_credentials.env"
ZABOB_DEFAULT_COMPOSE: Final[Path] = ZABOB_DOCKER_DIR / "docker-compose.yml"

ZABOB_BIN_DIR: Final[Path] = ZABOB_ROOT / 'bin'

ZABOB_NODE_BIN: Final[Path] = ZABOB_MODULES_DIR / 'node_modules/.bin'
ZABOB_MARKSERV: Final[Path] = ZABOB_NODE_BIN / 'markserv'

ZABOB_BROWSE_PORT_FILE = ZABOB_ROOT / '.browse.html.port'
ZABOB_BROWSE_RELOAD_FILE = ZABOB_ROOT / '.browse.reload.port'
ZABOB_BROWSE_PID_FILE = ZABOB_ROOT / '.browse.pid'
ZABOB_BROWSE_LOG_FILE = ZABOB_ROOT / '.browse.log'

VENV_DIR: Final[Path] = ZABOB_MODULES_DIR / '.venv'
if VENV_DIR.is_dir():
    # If the virtual environment is already created, we need to
    # activate it.

    os.environ['VIRTUAL_ENV'] = str(VENV_DIR)
    os.environ['PATH'] = str(VENV_DIR / 'bin') + os.pathsep + os.environ['PATH']
    sys.path.insert(0, str(VENV_DIR / 'bin'))
    pyversion = sys.version_info
    python_lib = f'python{pyversion.major}.{pyversion.minor}'
    libs = VENV_DIR / 'lib' / python_lib / 'site-packages'
    sys.path.insert(-2, str(libs))


def _version(version: Version|str) -> Version:
    """
    Convert a version to a semver.Version object.

    Args:
        version (Version|str): The version to convert.

    Returns:
        Version: The converted version.
    """
    if isinstance(version, Version):
        return version
    return Version.parse(version, optional_minor_and_patch=True)


HOUDINI_PROJECTS: Final[Mapping[Version, Path]] = {
    _version(p.name[1:]): p
    for p in ZABOB_HOUDINI_DIR.glob("h*.*")
    if p.is_dir()
}

SUBPROJECTS: Final[tuple[Path, ...]] =tuple(
    p
    for pattern in (
            'zabob-modules',
            'mcp-server',
            'zabob-chat',
            'houdini/h*.*',
            'houdini/zcommon',
            'houdini/hdas'
            "docs",
        )
    for p in ZABOB_ROOT.glob(pattern)
    if p.is_dir()
)
'''
Paths to all the subproject directories.
'''

ALLPROJECTS: Final[tuple[Path, ...]] = (
    ZABOB_ROOT,
    *SUBPROJECTS,
)
'''
Paths to all the subproject directories, including the root project directory.
'''

__all__: Final[tuple[str, ...]] = (
    "ZABOB_CORE_DIR",
    "ZABOB_MODULES_DIR",
    "ZABOB_ROOT",
    "ZABOB_PACKAGE_FILE",
    "ZABOB_DOCKER_DIR",
    "HOUDINI_PROJECTS",
    "SUBPROJECTS",
    "ALLPROJECTS",
    "ZABOB_HOUDINI_20_5_DIR",
    "ZABOB_DOCS_DIR",
    "ZABOB_IMAGES_DIR",
    "ZABOB_DEFAULT_CREDENTIALS",
    "ZABOB_DEFAULT_COMPOSE",
    "ZABOB_BIN_DIR",
    "ZABOB_NODE_BIN",
    "ZABOB_MARKSERV",
    "ZABOB_BROWSE_PORT_FILE",
    "ZABOB_BROWSE_RELOAD_FILE",
    "ZABOB_BROWSE_PID_FILE",
    "ZABOB_BROWSE_LOG_FILE",
)
