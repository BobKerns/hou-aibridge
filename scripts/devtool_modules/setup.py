'''
Implementation of the `devtool setup` command line tool.

This command is used to set up the development environment for the project.
'''


from collections.abc import Iterator
from itertools import count
import os
from pathlib import Path
import subprocess
import sys
from typing import IO, Final, NamedTuple, cast
from hashlib import blake2b, file_digest

import click
import tomlkit
import tomlkit.container
from tomlkit.toml_file import TOMLFile

if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from devtool_modules.node import node_version, node_path  # type: ignore # noqa: E402
from devtool_modules.paths import ALLPROJECTS, PROJECT_ROOT, SUBPROJECTS
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

type Offsets = tuple[Iterator[int], Iterator[int], Iterator[int]]
type ChecksumMap = dict[Path, str]

class DiffMaps(NamedTuple):
    """
    A class to hold the diff maps for the project and its subprojects.
    """
    added: set[Path]
    removed: set[Path]
    changed: set[Path]


_KEY_FILES: Final[tuple[str, ...]] = (
    'pyproject.toml', 'uv.lock', 'package.json', 'pnpm-lock.yaml',
    '.npmrc', '.envrc',
    '.node-version', '.python-version', '.houdini-version',
)

_FANOUT: Final[int] = max(len(ALLPROJECTS), len(_KEY_FILES)) + 1
_DEPTH: Final[int] = 3
_DIGEST_SIZE: Final[int] = 64
_INNER_DIGEST_SIZE: Final[int] = 64
_LEAF_SIZE: Final[int] = 0

def blake(person: bytes,
          node_depth: int,
          node_offset: int,
          last_node: bool) -> blake2b:
    """
    Create a BLAKE2b hash object.
    This is used to create a hash of the project and its subprojects.
    """
    return blake2b(digest_size=_DIGEST_SIZE, inner_size=_INNER_DIGEST_SIZE,
                   leaf_size=_LEAF_SIZE, fanout=_FANOUT, depth=_DEPTH,
                    person=person,
                    node_depth=node_depth, node_offset=node_offset,
                    last_node=last_node)

def end_node(node_depth: int,
             node_offset: int) -> bytes:
    """
    Create a BLAKE2b hash object for the end node.
    """
    hash = blake(
            person=b'None',
            node_depth=node_depth,
            node_offset=node_offset,
            last_node=True)
    return hash.digest()

def checksum_file(file: Path, offsets: Offsets, /,
                  node_depth: int=0):
    """
    Get the checksum of a file.
    This is used to check if the file has changed since the last time it was built.
    Args:
        file (Path|None): The file to check, or None if there are no more at this level.
        offsets (Offsets): The offsets to use for the checksum.
    """
    file = file.resolve()
    rel_file = file.relative_to(PROJECT_ROOT)
    person = str(rel_file.name).encode()[:16]
    hash = blake2b(digest_size=_DIGEST_SIZE, inner_size=_INNER_DIGEST_SIZE, leaf_size=_LEAF_SIZE,
                  fanout=_FANOUT, depth=_DEPTH,
                  person=person,
                  node_depth=node_depth,
                  node_offset=next(offsets[0]),
                  last_node=file is None)
    if file.exists():
        with file.open('rb') as f:
            file_digest(f, lambda: hash)
    yield None, hash.digest()

def checksum_subproject(subproject: Path, offsets: Offsets, /):
    """
    Get the checksum of a subproject.
    This is used to check if the subproject has changed since the last time it was built.
    """
    file = subproject.resolve()
    rel_file = file.relative_to(PROJECT_ROOT)
    person = str(rel_file).encode()
    hash = blake2b(digest_size=64, inner_size=64, leaf_size=0,
                   fanout=0, depth=3,
                   person=person,
                   node_depth=1, node_offset=next(offsets[1]))
    for file in _KEY_FILES:
        for path, chksum in checksum_file(subproject / file, offsets):
            hash.update(chksum)
            # Yield for our caller to include in the record
            yield path, chksum
    hash.update(end_node(0, next(offsets[0])))
    yield rel_file, hash.digest()

def checksum_project() :
    """
    Get the checksum of the project.
    This is used to check if the project has changed since the last time it was built.
    """
    offsets = (
        iter(count()), # Leafs
        iter(count()), # Ssubprojects
        iter(count()), # Project
    )
    hash = blake(
        person=b'PROJECT_ROOT',
        node_depth=2,
        node_offset=next(offsets[2]),
        last_node=False)
    for project in ALLPROJECTS:
        for path, chksum in checksum_subproject(project, offsets):
            # Yield for our caller to include in the record
            yield path, chksum
            hash.update(chksum)
    self_hash = blake(
        person=b'SELF',
        node_depth=1,
        node_offset=next(offsets[1]),
        last_node=True)
    with Path(__file__).open('rb') as f:
        file_digest(f, lambda: self_hash)
    yield Path('SELF'), self_hash.digest()
    hash.update(self_hash.digest())
    yield Path('PROJECT'), hash.digest()

def write_checksums(out: IO[str], /):
    """
    Write the checksums to a file.
    """
    for path, chksum in checksum_project():
        if path is not None:
            label = str(path)
            out.write(f"{label:28s} {chksum.hex()}\n")

@main.group("checksum")
def checksum():
    "Perform checksum operations on the project configuration."
    pass


@checksum.command(name='show')
def checksum_command() -> None:
    """
    Print the checksum of the project's configuration files.
    """
    write_checksums(sys.stdout)

@checksum.command(name='save')
def checksum_save() -> None:
    """
    Save the checksum of the project's configuration files to a file.
    """
    file = PROJECT_ROOT / '.checksums'
    with file.open('w') as out:
        write_checksums(out)


def read_checksums(in_: IO[str], /) -> ChecksumMap:
    """
    Read the checksums from a file.
    """
    return {
        Path(label): chksum
        for line in in_
        for label, chksum in (line.split(),)
    }

def diff_checksums(old: ChecksumMap, new: ChecksumMap, /) -> DiffMaps:
    """
    Compare the checksums of the project and its subprojects.
    """
    # Compare the checksums of the project and its subprojects.

    added = new.keys() - old.keys()
    removed = old.keys() - new.keys()
    changed = {
        path
        for path in old .keys() - removed
        if old[path] != new[path]
    }
    return DiffMaps(
        added=set(sorted(added)),
        removed=set(sorted(removed)),
        changed=set(sorted(changed)),
    )

@checksum.command(name='diff')
def checksum_diff() -> None:
    """
    Compare the checksums of the project and its subprojects.
    """
    file = PROJECT_ROOT / '.checksums'
    with file.open('r') as in_:
        old = read_checksums(in_)
    new = {
        path: hash.hex()
        for path, hash in checksum_project()
        if path is not None
    }
    diff = diff_checksums(old, new)
    if diff.added or diff.removed or diff.changed:
        print("Checksums differ:")
        for path in sorted(diff.added, key=str):
            print(f"  + {path}")
        for path in sorted(diff.removed, key=str):
            print(f"  - {path}")
        for path in sorted(diff.changed, key=str):
            print(f"  ~ {path}")
    else:
        print("Checksums are identical.")
        sys.exit(1)

if __name__ == '__main__':
    checksum_command()
