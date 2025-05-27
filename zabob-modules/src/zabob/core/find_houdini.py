#!/usr/bin/env uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "click",
#     "semver",
# ]
# ///
import sys
from pathlib import Path

import click
from semver import Version
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import shared types and utilities
from zabob.core.utils import OptionalType, SemVerParamType
from zabob._find.types import HoudiniInstall, _version

# Conditionally import the platform-specific module
if sys.platform == 'linux':
    from zabob._find._linux import find_installations # type: ignore
elif sys.platform == 'darwin':
    from zabob._find._macos import find_installations # type: ignore
elif sys.platform == 'win32':
    from zabob._find._windows import find_installations # type: ignore
else:
    def find_installations():
        """Placeholder for unsupported platforms."""
        return {}, {}

def find_houdini_installations() -> dict[Version, HoudiniInstall]:
    """
    Find all installed Houdini versions (20.5+ with Python 3.11+) on the system.

    Returns:
        Dictionary mapping Houdini version strings to HoudiniInstall objects.
        Both full version numbers and major.minor versions are included.
    """
    return find_installations()


def get_houdini(version: Version|None = None) -> HoudiniInstall:
    """
    Get a specific Houdini installation, or latest if version is None.

    Args:
        version: Specific version to get ("20.5" or "20.5.584")

    Returns:
        HoudiniInstall containing paths to the installation

    Raises:
        FileNotFoundError: If no matching installation found
    """
    installations = find_houdini_installations()

    if not installations:
        raise FileNotFoundError("No Houdini installations found on this system")

    if version is None:
        # Return the latest version (last in sorted dictionary)
        return max(installations.values(), key=lambda x: x.houdini_version)

    # Try exact match
    v = _version(version)
    if v in installations:
        return installations[v]

    raise FileNotFoundError(f"No Houdini installation matching version {v} found")



@click.command()
@click.argument('version',
                type=OptionalType(SemVerParamType(min_parts=2)),
                default=None,
                required=False)
def show_houdini(version: Version|None=None):
    """
    Command-line interface to find Houdini installations.

    Args:
        version: Specific version to get ("20.5" or "20.5.584")
    """
    try:
        houdini = get_houdini(version)
        print(f"Found Houdini installation: {houdini}")
        print(f"Installed applications: {', '.join(houdini.app_paths.keys())}")
        title = 'Python Version'
        print(f"  {title:>14s}: {houdini.python_version}")
        title = 'Version Dir'
        version_dir = houdini.version_dir
        print(f"  {title:>14s}: {version_dir}")
        for key in (
                    'exec_prefix',
                    'bin_dir',
                    'hython',
                    'hfs_dir',
                    'lib_dir',
                ):

            title = key.replace('_', ' ').title()
            title = title.replace('hfs', 'HFS')
            print(f"      {title:>14s}: {Path(getattr(houdini, key)).relative_to(version_dir)}")

    except FileNotFoundError as e:
        print(e)

@click.command()
def list_houdini_installations():
    """
    List all installed Houdini versions on the system.
    """
    installations = find_houdini_installations()
    if not installations:
        print("No Houdini installations found.")
        return

    for version, install in sorted(installations.items(), key=lambda x: x[0]):
        if version.patch != 0:
            # MM.nn.0 versions are generic, not specific builds
            print(f"{version}: (Python {install.python_version})")
            print(f"    {install.version_dir}")


if __name__ == "__main__":
    show_houdini()
