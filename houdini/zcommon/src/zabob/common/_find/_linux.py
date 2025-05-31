'''
Find where Houdini is hiding on Linux
'''

from collections.abc import Iterable
from contextlib import suppress
from pathlib import Path

from semver import Version
from zabob.common._find.types import (
    HoudiniInstall,
    _get_houdini_version, _group_by_major_minor,
    _parse_pyversion, _version,
)


def find_installations() -> dict[Version, HoudiniInstall]:
    """Find Houdini installations on Linux systems."""
    # installations: dict[str, HoudiniInstall] = {}
    # Common Linux installation paths

    base_dir = Path('/opt')
    installations = {
        install.houdini_version: install
        for version_dir in base_dir.glob('hfs*.*')
        for install in _process_installation(version_dir)
    }

    return installations | {
            v: max(installs, key=lambda i: i.houdini_version)
            for v, installs in _group_by_major_minor(installations).items()
        }

def _process_installation(version_dir: Path) -> Iterable[HoudiniInstall]:
    hfs_dir = version_dir
    # Standard Linux directory structure
    bin_dir = hfs_dir / 'bin'
    hython_path = bin_dir / 'hython'

    if not hython_path.exists():
        return

    with suppress(TypeError, ValueError):
        # If we can't parse this version, we skip this installation.
        # Extract version from directory name or hython
        # Try to extract version from directory or hython
        houdini_version = _get_houdini_version(hfs_dir.name)
        if houdini_version == "unknown":
            return

        # Find Python library directories using glob pattern
        python_version, python_lib = max((
                (v, dir)
                for dir in hfs_dir.glob('houdini/python*.*libs')
                for v in _parse_pyversion(dir)
            ),
            key=lambda p: p[0],
            default=(Version(0), hfs_dir),
            )

        if python_version.major < 3:
            return


        # Create the installation entry
        yield HoudiniInstall(
            houdini_version=houdini_version,
            python_version=_version(python_version),
            version_dir=version_dir,
            exec_prefix=version_dir, #TODO: Verify this
            hfs_dir=version_dir,
            hdso_libs= hfs_dir / 'dsolib',
            bin_dir=bin_dir,
            hh_dir=hfs_dir / 'houdini',
            toolkit_dir=hfs_dir / 'toolkit',
            config_dir=hfs_dir / 'config',
            sbin_dir=hfs_dir / 'sbin',
            hython=hython_path,
            python_libs=python_lib,
            app_paths={},
        )
