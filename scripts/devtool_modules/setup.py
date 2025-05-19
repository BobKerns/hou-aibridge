'''
Implementation of the `devtool setup` command line tool.

This command is used to set up the development environment for the project.
'''


import os
from pathlib import Path
import subprocess
from typing import cast

import click
import tomlkit
import tomlkit.container
from tomlkit.toml_file import TOMLFile

from devtool_modules.node import node_path, node_version
from devtool_modules.paths import PROJECT_ROOT, SUBPROJECTS
from devtool_modules.subproc import run
from devtool_modules.utils import QUIET, rmdir
from devtool_modules.main import main


@main.command(name='setup')
@click.option('--force',
              is_flag=True,
              help="Force setup, removing existing directories.")
@click.option('--dry-run',
              is_flag=True,
              help="Show what would be done, but do not actually do it.")
def setup(
    force: bool=False,
    dry_run: bool=False,
) -> None:
    "Set up the project. This includes installing dependencies and setting up the server."
    if not QUIET.enabled:
        output = subprocess.DEVNULL
    else:
        output = None
    node_env = os.environ.copy()
    version = node_version()
    nvm_dir = Path.home() / '.nvm'
    node_env['NVM_DIR'] = str(nvm_dir)
    node_env['NODE_VERSION'] = version
    nvm_setup = nvm_dir / 'nvm.sh'
    run('bash', '-c', nvm_setup, ';', 'nvm', 'install', version,
        cwd=PROJECT_ROOT,
        stdout=output,
        stderr=output,
        dry_run=dry_run,
    )
    nvm_node = node_path()
    BIN = PROJECT_ROOT / 'bin'
    bin_node = BIN / 'node'
    QUIET("Symlinking node to bin directory...")
    if not dry_run:
        bin_node.unlink(missing_ok=True)
        bin_node.symlink_to(nvm_node)

    # None of these should be in the repository root.
    # They are all in the subprojects.
    # We remove them to avoid conflicts with the subprojects.
    rmdir(
        PROJECT_ROOT / '.venv',
        PROJECT_ROOT / 'node_modules',
        PROJECT_ROOT / 'pnpm-lock.yaml',
        PROJECT_ROOT / 'uv.lock',
        PROJECT_ROOT / 'houdini_versions_cache.json',
        PROJECT_ROOT / 'requirements.txt',
        dry_run=dry_run,
    )
    uv_env = os.environ.copy()
    del uv_env['VIRTUAL_ENV']
    for subproject in SUBPROJECTS:
        QUIET(f"Setting up {subproject.stem}...")
        pyproject = subproject / 'pyproject.toml'
        package = subproject / 'package.json'
        if force:
            rmdir(
                *(subproject / d
                  for d in ('node_modules', 'dist', 'build')),
                *(subproject.glob('**/*.egg-info')),
                *(subproject.glob('__pycache__')),
                dry_run=dry_run,
            )
        if pyproject.exists():
            file = TOMLFile(pyproject)
            toml = file.read()
            project = cast(tomlkit.container.Container, toml['project'])
            use_hython = project.get('use-hython', False)
            if use_hython:
                # Use hython to create the virtual environment.
                run('hython', '-m', 'venv', '.venv', '--without-pip',
                    cwd=subproject,
                    env=uv_env,
                    stdout=output,
                    stderr=output,
                    dry_run=dry_run,
                )
            dry_run_flag = ('--dry-run',) if dry_run else ()
            run('uv', 'sync', *dry_run_flag,
                cwd=subproject,
                env=uv_env,
                stdout=output,
                stderr=output,
            )
        if package.exists():
            run('pnpm', 'install',
                cwd=subproject,
                env=node_env,
                stdout=output,
                stderr=output,
                dry_run=dry_run,
            )
