'''
The `devtool node` command.
'''


import json
from pathlib import Path
import sys

import click

from devtool_modules.paths import BIN_DIR, PROJECT_ROOT, SUBPROJECTS
from devtool_modules.subproc import run
from devtool_modules.main import main


@main.group(name='node')
def node_group() -> None:
    '''
    Perform operations related to configuring using node.js
    '''
    pass


@node_group.command(name='version')
@click.option('--range', is_flag=True,
              help="Print the range of node versions supported by this project.")
def show_node_version(range) -> None:
    """
    Print the version of node.js configured for this project in the package.json file.

    This also updates the .nvmrc file to match the version in package.json.
    """
    print(node_version(range))


def node_version(range: bool=False) -> str:
    root_pkg = PROJECT_ROOT / 'package.json'
    with root_pkg.open('r') as f:
        pkg = json.load(f)
    version= pkg.get('engines', {}).get('node', '23.11.0')
    if not range:
        # If we are not in range mode, we want to use the exact version.
        # We remove the prefix and suffixes, qne pick the minimum version
        # of the first element of the range.
        version = version.strip().lstrip('^>=<')
        version = version.split(',', 1)[0]
    return version

@node_group.command(name='update')
def node_update() -> None:
    """
    Update the node version to match the package.json file..
    """
    version = node_version()
    bin_node = BIN_DIR / 'node'
    bin_node.unlink(missing_ok=True)
    bin_node.symlink_to(version)
    for subproject in (PROJECT_ROOT, *SUBPROJECTS):
        package = subproject / 'package.json'
        if package.exists():
            nvmrc = PROJECT_ROOT / '.nvmrc'
            with nvmrc.open('w') as f:
                f.write(version)
            print(f"{subproject.stem}: Updated .nvmrc to {version}")
            run('pnpm', 'install', cwd=subproject, shell=False)
    run('pnpm', 'install')

@node_group.command(name='path')
@click.option('--version', is_flag=False, cls=click.Option,
              help="Specify the version of node.js to use.")
def node_path_command(version:str|None=None) -> None:
    """```
    Print the path to the node executable.

    Returns 0 if the node executable is found, non-zero otherwise.
    """
    path = node_path(version)
    print(path)
    if not path.exists():
        print(f"Node executable not found at {path}.", file=sys.stderr)
        sys.exit(2)
    print(path)
    sys.exit(0)

def node_path(version: str|None=None) -> Path:
    "Return the path to the node executable."
    if version is None:
        version = node_version()
    nvm_dir = Path.home() / '.nvm'
    node_path = nvm_dir / 'versions' / version / 'bin' / 'node'
    return node_path.resolve()

@node_group.command(name='run')
@click.argument('args', nargs=-1)
def node_run(args: tuple[str,...]) -> None:
    "Run the node command."
    node = BIN_DIR / 'node'
    run(node, *args, shell=False)
