'''
Find Houdini installations on macOS systems.
This module contains functions to locate Houdini installations on macOS systems.
'''
from collections.abc import Iterable
from contextlib import suppress
from pathlib import Path
import re

from semver import Version

from hou_aibridge._find.types import (
    HoudiniInstall,
    _get_houdini_version,
    _group_by_major_minor,
    _parse_pyversion,
)


_RE_APP_NAME = re.compile(r'^(?:Houdini ?)(.*) *(\d+\.\d+.\d+).app$')


def find_installations() -> dict[Version, HoudiniInstall]:
    '''
    Find Houdini installations on macOS systems.
    This function searches for Houdini installations in the standard directories
    and returns a dictionary mapping Houdini version strings to HoudiniInstall objects.
    The dictionary includes both full version numbers and major.minor versions.
    The major.minor versions point to the latest builds for that major.minor version.
    '''

    # Base directories to search
    # The standard installation is for e.g. /Applications/Houdini/Houdini20.5.584
    # I don't think it's worth looking for alternate installation locations, as
    # those will not play well with the Houdini launcher or installer, which uses
    # this layout to allow smooth upgrades and multiple versions.
    # The Houdini launcher will also create a symlink in /Applications/Houdini/Current
    # to the latest version, so we can use that to find the latest build.
    base_dir = Path('/Applications/Houdini')
    if not base_dir.exists():
        return {}


    installations = {
        install.houdini_version: install
        for version_dir in base_dir.glob('Houdini*.*')
        for install in _process_installation(version_dir)
    }

    # Add in the latest builds for each major.minor version
    return installations | {
            v: max(installs, key=lambda i: i.houdini_version)
            for v, installs in _group_by_major_minor(installations).items()
        }


def _process_installation(version_dir: Path) -> Iterable[HoudiniInstall]:
    """
    Process a potential Houdini installation directory.
    """
    # Validate the directory structure
    if not version_dir.is_dir():
        return
    frameworks = version_dir / "Frameworks"
    if not frameworks.exists() or not frameworks.is_dir():
        return
    hfs_dir = frameworks / 'Houdini.framework/Resources'
    if not hfs_dir.exists() or not hfs_dir.is_dir():
        return
    bin_dir = hfs_dir / 'bin'
    if not bin_dir.exists() or not bin_dir.is_dir():
        return
    hython_path = bin_dir / "hython"
    if not hython_path.exists():
        # We need to reject this version. It may be a partially-deleted install.
        return

    # We could collect all the frameworks and check for the Houdini.framework
    # but that would be hard to apply cross-platform and probably not useful.
    # But the apps are user-visible artifacts that may be discussed.
    app_paths = {
        m.group(1): app
        for app_dir in (version_dir,
                        version_dir / 'Utilities',
                        version_dir / 'Administrative Tools')
        for app in app_dir.glob("*.app")
        for m in (_RE_APP_NAME.match(app.name),)
        if m is not None
    }


    with suppress(ValueError, TypeError):
        # If we can't parse the version, skip this installation.
        houdini_version = _get_houdini_version(version_dir.name)

        # Pick the highest version of Python 3.x libs. We doh't need to ask for the exact
        # version; we can do that later if we need it. Startimg hython is expensive.
        python_version, lib_dir = max((
                                (v, dir)
                                for dir in hfs_dir.glob('houdini/python*.*libs')
                                for v in _parse_pyversion(dir)
                            ),
            key=lambda p: p[0],
            default=(Version(0), hfs_dir),
        )
        # We won't reject python versions <3.11, but we can't use them.
        # We can still report them.
        yield HoudiniInstall(
            houdini_version=houdini_version,
            python_version=python_version,
            version_dir=version_dir,
            bin_dir=bin_dir,
            hython=hython_path,
            hfs_dir=hfs_dir,
            lib_dir=lib_dir,
            app_paths=app_paths,
        )
