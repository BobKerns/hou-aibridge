'''
Commands relating to Houdini
'''

from importlib import resources
import shutil
import stat
import sys
from pathlib import Path
from configparser import ConfigParser

import click
from semver import Version


from zabob.houdini_versions import cli as houdini_cli
from zabob.find_houdini import show_houdini
from zabob.main import main
from zabob.paths import HOUDINI_PROJECTS, ZABOB_HOUDINI_DIR
from zabob.subproc import run

@main.group('houdini')
def houdini_commands():
    """
    Houdini commands.
    """
    pass

def install_hython_launcher(venv_path, system_python=None):
    """Install the hython launcher to the specified venv bin directory.

    Args:
        venv_path: Path to the virtual environment
        system_python: Path to system Python (defaults to system Python)
    """
    # Get system Python path if not provided
    if system_python is None:
        system_python = getattr(sys, '_base_executable', sys.executable)

    venv_path = Path(venv_path).resolve()
    bin_dir = venv_path / "bin"
    target_path = bin_dir / "hython"

    # Get template file path
    with resources.path("zabob.data", "hython") as src_path:
        with open(target_path, 'w') as target:
            # Write custom shebang
            target.write(f"#!{system_python}\n")

            # Copy the rest (skipping first line)
            with open(src_path, 'r') as source:
                # Skip the first line (original shebang)
                source.readline()

                # Copy the rest efficiently
                shutil.copyfileobj(source, target)

    # Make executable
    target_path.chmod(target_path.stat().st_mode | stat.S_IEXEC)

    return target_path

def configure_houdini_venv(venv_path, houdini_path, system_python=None):
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
    hython_path = install_hython_launcher(venv_path, system_python)

    # Update pyenv.cfg with Houdini information
    pyenv_cfg_path = venv_path / "pyvenv.cfg"

    # Read existing configuration
    config = ConfigParser()
    # ConfigParser requires section headers, but pyvenv.cfg doesn't have them
    # Add a default section to parse it correctly
    with open(pyenv_cfg_path, 'r') as f:
        config_content = '[DEFAULT]\n' + f.read()

    config.read_string(config_content)

    # Create a hython section with Houdini home
    if 'hython' not in config:
        config.add_section('hython')

    config.set('hython', 'home', str(houdini_path))

    # Write back to pyenv.cfg without the [DEFAULT] section
    with open(pyenv_cfg_path, 'w') as f:
        # Write all key-value pairs without section headers
        for key, value in config['DEFAULT'].items():
            f.write(f"{key} = {value}\n")

        # Write the hython section with header
        f.write("\n[hython]\n")
        for key, value in config['hython'].items():
            f.write(f"{key} = {value}\n")

    # Update python symlink if needed
    # This is optional - only do this if you want to replace the default Python
    # with the Houdini Python (which could cause compatibility issues)

    return hython_path

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

            # TODO: 1) Check if the version is installed, using the
            # get_houdini function.
            # 2) If not installed, download (if not cached) and install it.
            # 3) Get the path to the Houdini installation with the
            # get_houdini function.
            # 4) Use this instead of the following line to configure the venv.
            houdini_path = HOUDINI_PROJECTS[houdini_version]

            # Create the venv using UV if it doesn't exist
            if not venv_path.exists():
                print(f"Creating virtual environment at {venv_path}")
                run('uv', 'venv', venv_path)
            else:
                print(f"Using existing virtual environment at {venv_path}")

            # Configure the venv for Houdini
            return configure_houdini_venv(venv_path, houdini_path)

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

for name, command in houdini_cli.commands.items():
    # Register the command with the main group
    houdini_commands.add_command(command, name)
    houdini_commands.add_command(show_houdini, 'show')

    # Add the command to the Houdini commands gr
