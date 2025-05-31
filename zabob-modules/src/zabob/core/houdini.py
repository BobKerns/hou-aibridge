'''
Commands relating to Houdini
'''

from importlib import resources
import os
import shutil
import site
import stat
import sys
from pathlib import Path
from configparser import ConfigParser, UNNAMED_SECTION

import click
from semver import Version


from zabob.common._find.types import HoudiniInstall
from zabob.common.find_houdini import get_houdini, list_houdini_installations, show_houdini
from zabob.common.subproc import run
from zabob.common.hython import hython
from zabob.core.houdini_versions import cli as houdini_cli, download_houdini_installer
from zabob.core.main import main
from zabob.core.paths import HOUDINI_PROJECTS, ZABOB_HOUDINI_DIR

@main.group('houdini')
def houdini_commands():
    """
    Houdini commands.
    """
    pass

def install_hython_launcher(venv_path, system_python=None) -> tuple[Path, Path]:
    """Install the hython launcher to the specified venv bin directory.

    Args:
        venv_path: Path to the virtual environment
        system_python: Path to system Python (defaults to system Python)

    Returns:
        Tuple containing:
            - Path to the hython launcher script
            - Path to the bin directory of the Houdini installation

    """
    # Get system Python path if not provided
    if system_python is None:
        system_python = getattr(sys, '_base_executable', sys.executable)

    venv_path = Path(venv_path).resolve()
    bin_dir = venv_path / "bin"
    target_path = bin_dir / "hython"

    with resources.open_text("zabob.data", "sitecustomize.py") as src:
        with open(venv_path / "lib" / "sitecustomize.py", 'w') as target:
            # Write the sitecustomize.py content
            shutil.copyfileobj(src, target)

    # Get template file path
    with resources.open_text("zabob.data", "hython") as src:
        with open(target_path, 'w') as target:
            # Write custom shebang
            target.write(f"#!{system_python}\n")
                # Skip the first line (original shebang)
            src.readline()

            # Copy the rest efficiently
            shutil.copyfileobj(src, target)

    # Make executable
    target_path.chmod(target_path.stat().st_mode | stat.S_IEXEC)

    return target_path, bin_dir

def configure_houdini_venv(venv_path: Path,
                           houdini_path: Path,
                           site_libs_path: Path,
                           lib_path: Path,
                           system_python=None):
    """
    Configure a virtual environment for Houdini.

    Args:
        venv_path: Path to the virtual environment
        houdini_path: Path to the Houdini installation
        system_python: Path to system Python (defaults to auto-detected)

    Returns:
        Path to the hython launcher script
    """

    venv_path = Path(venv_path).resolve()
    houdini_path = Path(houdini_path).resolve()

    # Install the hython launcher
    hython_path, bin_dir = install_hython_launcher(venv_path, system_python)

    # Update pyenv.cfg with Houdini information
    pyenv_cfg_path = venv_path / "pyvenv.cfg"

    # Read existing configuration
    config = ConfigParser(allow_unnamed_section=True)
    config.read(pyenv_cfg_path)

    # Create a hython section with Houdini home
    if 'hython' not in config:
        config.add_section('hython')

    config.set('hython', 'hython', str(houdini_path))
    config.set(UNNAMED_SECTION, 'home', str(houdini_path.parent ))
 # Remove existing home if it exists


    # Write back to pyenv.cfg without the [DEFAULT] section
    with pyenv_cfg_path.open('w') as f:
        config.write(f)

    pth_path = site_libs_path / '_houdini.pth'
    with pth_path.open('w') as f:
        f.write(str(lib_path) + os.linesep)

    hython_path = bin_dir / 'hython'
    for p in ('python', 'python3'):
        # Remove existing symlinks if they exist
        python_path = venv_path / 'bin' / p
        python_path.unlink(missing_ok=True)
        # Create a symlink to the hython launcher
        python_path.symlink_to(hython_path.relative_to(venv_path / 'bin'))
    return hython_path

def get_hython_paths(version: Version|None,
                    install: bool=False) -> HoudiniInstall:
    """
    Get the path to the hython launcher for a specific Houdini version.
    If the version is not installed, it will raise an error.
    If `install` is True, it will download (if not cached) the version
    and install it before returning the path.
    """
    try:
        try:
            houdini: HoudiniInstall= get_houdini(version)
        except FileNotFoundError:
            if not install:
                raise FileNotFoundError(f"No Houdini installation matching version {version} found")
            else:
                # If install is True, we should download and install the version
                if version is None:
                    # Pick the latest version we have support for
                    version = max(HOUDINI_PROJECTS.keys())
                houdini = install_houdini(version)
        return houdini
    except Exception as e:
        raise RuntimeError(f"Failed to get Houdini installation: {e}")


def install_houdini(version: Version) -> HoudiniInstall:
    '''
    Install a specific Houdini version.
    This will download the installer if not cached, and then run it.

    Args:
        version: The Houdini version to install (e.g., "20.5.584")
    Returns:
        Path to the installed Houdini directory.
    '''
    installer = download_houdini_installer(version)
    if not installer.exists():
        raise FileNotFoundError(f"Houdini installer for version {version} not found at {installer}")
    # Run the installer
    print(f"Running Houdini installer for version {version} at {installer}")
    run(installer, '--install', '--accept-eula', '--no-gui', '--no-shortcuts')
    return get_houdini(version)


def setup_houdini_venv_from_current(directory: Path|None=None,
                                    install: bool=False):
    """
    Search upward from the current directory to find a .houdini-version file,
    create a venv, and configure it for Houdini.

    Returns:
        Path to the hython launcher script

    Raises:
        RuntimeError: If the search reaches ZABOB_HOUDINI_DIR without finding .houdini-version
    """
    if directory is None:
        directory = Path.cwd()

    # Search upward
    while True:
        # Check if .houdini-version exists in this directory
        version_file = directory / '.houdini-version'
        if version_file.exists():
            # Found it! Read the version
            houdini_version = Version.parse(version_file.read_text().strip(),
                                            optional_minor_and_patch=True)

            # Determine venv path - same directory as .houdini-version
            venv_path = directory / '.venv'

            # Check if the Houdini version exists in our projects
            # This checks if we have configured our setup correctly.
            # It does not give us the corresponding Houdini path.
            if houdini_version not in HOUDINI_PROJECTS:
                raise RuntimeError(f"Houdini version {houdini_version} not found in available projects")

            houdini = get_hython_paths(
                houdini_version,
                install=install
            )

            # Create the venv using UV if it doesn't exist
            if not venv_path.exists():
                print(f"Creating virtual environment at {venv_path}")
                run('uv', 'venv', venv_path)
            else:
                print(f"Using existing virtual environment at {venv_path}")

            # Configure the venv for Houdini
            houdini_path = houdini.hython
            site_lib_path = venv_path / 'lib' / f'python{houdini.python_version.major}.{houdini.python_version.minor}' / 'site-packages'
            site_lib_path.mkdir(parents=True, exist_ok=True)
            lib_dir = houdini.lib_dir
            return configure_houdini_venv(venv_path, houdini_path, site_lib_path, lib_dir)

        # If we've reached ZABOB_HOUDINI_DIR, stop and raise an error
        if directory.samefile(ZABOB_HOUDINI_DIR):
            raise RuntimeError("Reached ZABOB_HOUDINI_DIR without finding .houdini-version file")

        # Move up one directory
        parent_dir = directory.parent

        # If we've reached the root directory, stop
        if parent_dir == directory:
            raise RuntimeError("Reached filesystem root without finding .houdini-version file")

        directory = parent_dir

@houdini_commands.command('setup-venv')
@click.option('--directory', '-d',
              type=click.Path(exists=True, file_okay=False, path_type=Path),
              default=Path.cwd(),
              help="Directory to start.")
@click.option('--install/--no-install', '-i/-n', default=False,
              help="Install the virtual environment if it doesn't exist (default: no install)")
def setup_houdini_venv_cmd(directory: Path|None=None,
                          install: bool=False):
    """Setup a virtual environment for Houdini based on .houdini-version file."""
    directory = directory or Path.cwd()
    try:
        hython_path = setup_houdini_venv_from_current(
            directory=directory,
            install=install
        )
        print(f"Houdini virtual environment setup complete. Hython launcher: {hython_path}")
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)

houdini_commands.add_command(show_houdini, 'show-houdini')
houdini_commands.add_command(list_houdini_installations, 'installations')
houdini_commands.add_command(hython, 'hython')
for name, command in houdini_cli.commands.items():
    # Register the command with the main group
    houdini_commands.add_command(command, name)


    # Add the command to the Houdini commands gr
