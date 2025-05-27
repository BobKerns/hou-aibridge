'''
Path constants for Zabob project directories and files, accessible to
all supported python versions.
'''

from pathlib import Path

ZABOB_COMMON_DIR: Path = Path(__file__).resolve().parent
_ZABOB_PKG_DIR: Path = ZABOB_COMMON_DIR.parent
_ZABOB_SRC_DIR: Path = _ZABOB_PKG_DIR.parent
ZABOB_ZCOMMON_DIR: Path = _ZABOB_SRC_DIR.parent
ZABOB_HOUDINI_DIR: Path = ZABOB_ZCOMMON_DIR.parent
ZABOB_ROOT: Path = ZABOB_HOUDINI_DIR.parent

ZABOB_OUT_DIR: Path = ZABOB_ROOT / "out"
