'''
Find Houdini hiding on Windows
'''

from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from itertools import chain
from functools import reduce
import os

from semver import Version

from hou_aibridge._find._macos import suppress
from hou_aibridge._find.types import (
    HoudiniInstall,
    _get_houdini_version, _group_by_major_minor, _if_exists, _parse_pyversion,
)
from hou_aibridge._find.types import _get_major_minor

def _by_regkey():
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Side Effects Software') as key: # type: ignore
            i = 0
            while True:
                try:
                    version_key_name = winreg.EnumKey(key, i) # type: ignore
                    with winreg.OpenKey(key, version_key_name) as version_key: # type: ignore
                        try:
                            install_path, _ = Path(winreg.QueryValueEx(version_key, 'InstallPath')) # type: ignore
                            # Check if the installation path is valid
                            # Process the installation
                            yield install_path
                        except OSError:
                            pass
                    i += 1
                except OSError:
                    break
    except OSError:
        pass

def _by_directory():
    """Find Houdini installations in standard directories."""
    # Check the standard installation directories
    program_files = os.environ.get('PROGRAMFILES', r'C:\Program Files')
    base_dir = Path(program_files) / 'Side Effects Software'
    if not base_dir.exists():
        return

    for houdini_dir in base_dir.glob('Houdini*'):
        if houdini_dir.is_dir():
            yield houdini_dir


def find_installations() -> dict[Version, HoudiniInstall]:
    """Find Houdini installations on Windows systems."""
    installations: dict[Version, HoudiniInstall] = {
        install.houdini_version:install
        for path in chain(_by_regkey(), _by_directory())
        for install in _process_installation(path)
    }

    latest_builds = reduce(lambda a, i: (a[i.houdini_version].append(i), a)[1],
                            installations.values(),
                            defaultdict(list))
    latest_builds: dict[Version, list[HoudiniInstall]] = defaultdict(list)
    # Group installations by major.minor version
    for version, install in installations.items():
        major_minor = _get_major_minor(version)
        latest_builds[major_minor].append(install)

    # Add in the latest builds for each major.minor version
    return installations | {
            v: max(installs, key=lambda i: i.houdini_version)
            for v, installs in _group_by_major_minor(installations).items()
        }

def _process_installation(version_dir: Path) -> Iterable[HoudiniInstall]:
    """Process a potential Houdini installation directory."""
    bin_dir = version_dir / 'bin'
    hython_path = bin_dir / 'hython.exe'

    if not hython_path.exists():
        return

    with suppress(TypeError, ValueError):
        # If we can't parse this version, we skip this installation.
        # Extract version from directory name or hython
        houdini_version = _get_houdini_version(version_dir.name)
        if houdini_version.major == 0:
            return

        # Find Python lib dirs using glob
        python_version, lib_dir = max((
                            (version, path)
                            for path in version_dir.glob('houdini/python*.*libs')
                            for version in _parse_pyversion(path)
                            ),
                    key=lambda p: p[0],
                    default=(Version(0), version_dir),
                )
        if python_version.major < 3:
            return

        app_names ={
            "GPlay": "gplay",
            "Apprentice": "happrentice",
            "Education": "heducation",
            "Indie": "houdini_indie",
            "FX": "houdinifx",
            "Core": "houdinicore",
            "Viewer": "hview",
            "MPlayer": "mplay",
        }

        app_paths = {
            app_name: exe
            for app_name, file in app_names.values()
            for exe in _if_exists(version_dir / file, '.exe')
        }

        # Create installation entry
        yield HoudiniInstall(
            houdini_version=houdini_version,
            python_version=python_version,
            version_dir=version_dir,
            hfs_dir=version_dir,
            bin_dir=bin_dir,
            hython=hython_path,
            lib_dir=lib_dir,
            app_paths=app_paths,
        )
