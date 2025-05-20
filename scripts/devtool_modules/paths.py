'''
Useful pathname constants.
'''

from pathlib import Path
from typing import Final
from collections.abc import Mapping
import os
import sys

# Shared constants
DEVTOOL_DIR: Final[Path] = Path(__file__).resolve().parent
SCRIPTS_DIR: Final[Path] = DEVTOOL_DIR.parent
PROJECT_ROOT: Final[Path] = SCRIPTS_DIR.parent
CHAT_DIR: Final[Path] = PROJECT_ROOT / "vscode-chat"
PACKAGE_PATH: Final[Path] = CHAT_DIR / "package.json"

PROJECT_CHECKSUMS: Final[Path] = PROJECT_ROOT / ".checksums"
'''
Checksums for the project files.
This is used to check if the project files have changed.
'''


# Add useful path constants
DOCKER_DIR: Final[Path] = PROJECT_ROOT / "docker"
HOUDINI_20_5_DIR: Final[Path] = DOCKER_DIR / "houdini-20.5"
DOCS_DIR: Final[Path] = PROJECT_ROOT / "docs"
IMAGES_DIR: Final[Path] = DOCKER_DIR / "images"
DEFAULT_CREDENTIALS: Final[Path] = DOCKER_DIR / "sidefx_credentials.env"
DEFAULT_COMPOSE: Final[Path] = DOCKER_DIR / "docker-compose.yml"

BIN_DIR: Final[Path] = PROJECT_ROOT / 'bin'

NODE_BIN: Final[Path] = SCRIPTS_DIR / 'node_modules/.bin'
MARKSERV: Final[Path] = NODE_BIN / 'markserv'

PORT_FILE = PROJECT_ROOT / '.browse.html.port'
RELOAD_FILE = PROJECT_ROOT / '.browse.reload.port'
PID_FILE = PROJECT_ROOT / '.browse.pid'
LOG_FILE = PROJECT_ROOT / '.browse.log'

VENV_DIR: Final[Path] = SCRIPTS_DIR / '.venv'
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

HOUDINI_PROJECTS: Final[Mapping[str, Path]] = {
    p.name[1:]: p
    for p in PROJECT_ROOT.glob("houdini/h*.*")
    if p.is_dir()
}

SUBPROJECTS: Final[tuple[Path, ...]] =tuple(
    p
    for pattern in (
            'scripts',
            'mcp-server',
            'vscode-chat',
            'houdini/h*.*',
            "docs",
            'hdas'
        )
    for p in PROJECT_ROOT.glob(pattern)
    if p.is_dir()
)
'''
Paths to all the subproject directories.
'''

ALLPROJECTS: Final[tuple[Path, ...]] = (
    PROJECT_ROOT,
    *SUBPROJECTS,
)
'''
Paths to all the subproject directories, including the root project directory.
'''

__all__: Final[tuple[str, ...]] = (
    "DEVTOOL_DIR",
    "SCRIPTS_DIR",
    "PROJECT_ROOT",
    "PACKAGE_PATH",
    "DOCKER_DIR",
    "HOUDINI_PROJECTS",
    "SUBPROJECTS",
    "ALLPROJECTS",
    "HOUDINI_20_5_DIR",
    "DOCS_DIR",
    "IMAGES_DIR",
    "DEFAULT_CREDENTIALS",
    "DEFAULT_COMPOSE",
    "BIN_DIR",
    "NODE_BIN",
    "MARKSERV",
    "PORT_FILE",
    "RELOAD_FILE",
    "PID_FILE",
    "LOG_FILE",
)
