'''
Implementation of the `devtool setup` command line tool.

This command is used to set up the development environment for the project.
'''


from collections.abc import Generator, Iterator
from itertools import count
import os
from pathlib import Path
import subprocess
import sys
from typing import IO, Any, Final, Literal, NamedTuple, cast
from hashlib import blake2b, file_digest

import click

import tomlkit
import tomlkit.container
from tomlkit.toml_file import TOMLFile

if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from zabob.core.houdini import setup_houdini_venv_from_current
from zabob.core.node import node_version, node_path  # type: ignore # noqa: E402
from zabob.core.paths import ALLPROJECTS, ZABOB_CHECKSUMS, ZABOB_ROOT, SUBPROJECTS
from zabob.core.subproc import capture, run
from zabob.core.utils import DEBUG, QUIET, INFO, VERBOSE, rmdir
from zabob.core.main import main


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

    old = read_checksums(ZABOB_CHECKSUMS)
    new = {
        path: chksum.hex()
        for path, chksum in checksum_project()
        if path is not None
    }
    added, removed, changed = diff_checksums(old, new)
    if not added and not removed and not changed:
        INFO("Checksums are identical, skipping setup.")
        return
    if not QUIET.enabled:
        output = subprocess.DEVNULL
    else:
        output = None
    if VERBOSE.enabled:
        checksum_diff(old, new)
    node_env = os.environ.copy()
    version = node_version()
    nvm_dir = Path.home() / '.nvm'
    node_env['NVM_DIR'] = str(nvm_dir)
    node_env['NODE_VERSION'] = version
    nvm_setup = nvm_dir / 'nvm.sh'
    run('bash', '-c', nvm_setup, ';', 'nvm', 'install', version,
        cwd=ZABOB_ROOT,
        stdout=output,
        stderr=output,
        dry_run=dry_run,
    )
    nvm_node = node_path()
    BIN = ZABOB_ROOT / 'bin'
    bin_node = BIN / 'node'
    QUIET("Symlinking node to bin directory...")
    if not dry_run:
        bin_node.unlink(missing_ok=True)
        bin_node.symlink_to(nvm_node)

    # None of these should be in the repository root.
    # They are all in the subprojects.
    # We remove them to avoid conflicts with the subprojects.
    rmdir(
        ZABOB_ROOT / '.venv',
        ZABOB_ROOT / 'node_modules',
        ZABOB_ROOT / 'pnpm-lock.yaml',
        ZABOB_ROOT / 'uv.lock',
        ZABOB_ROOT / 'houdini_versions_cache.json',
        ZABOB_ROOT / 'requirements.txt',
        dry_run=dry_run,
    )
    uv_env = os.environ.copy()
    del uv_env['VIRTUAL_ENV']
    for subproject in SUBPROJECTS:
        relative = subproject.relative_to(ZABOB_ROOT)
        QUIET(f"Setting up {relative}...")
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
            dry_run_flag     = ('--dry-run',) if dry_run else ()
            if use_hython:
                 # Use hython to create the virtual environment.
                    QUIET("Creating hython virtual environment...")
                    # This currently fails. Ignore the error for now.
                    run('python', '-I', '-m', 'venv', '.venv',
                        cwd=subproject,
                        env=uv_env,
                        stdout=output,
                        stderr=output,
                        dry_run=dry_run,
                    )
                    setup_houdini_venv_from_current(
                    directory=subproject,
                    install=False
                )
                # with suppress(Exception):
                    # QUIET("Syncing hython virtual environment...")
                    # run('uv', 'sync', *dry_run_flag,
                    #     cwd=subproject,
                    #     env=uv_env,
                    #     stdout=output,
                    #     stderr=output,
                    # )
            else:
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
    checksum_save()

type _Offsets = tuple[Iterator[int], Iterator[int], Iterator[int]]
type ChecksumMap = dict[Path, str]
'''
A dictionary of checksums for the project and its subprojects.
The keys are the paths to the files, and the values are the checksums as strings
'''

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


def checksum_file(file: Path, offsets: _Offsets, /,
                  node_depth: int=0):
    """
    Get the checksum of a file.
    This is used to check if the file has changed since the last time it was built.
    Args:
        file (Path|None): The file to check, or None if there are no more at this level.
        offsets (Offsets): The offsets to use for the checksum.
    """
    file = file.resolve()
    rel_file = file.relative_to(ZABOB_ROOT)
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


def checksum_subproject(subproject: Path, offsets: _Offsets, /):
    """
    Get the checksum of a subproject.
    This is used to check if the subproject has changed since the last time it was built.
    """
    file = subproject.resolve()
    rel_file = file.relative_to(ZABOB_ROOT)
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
    this_dir = Path(__file__).resolve().parent
    data = this_dir / 'data'
    for p in (
            this_dir / 'setup.py',
            this_dir / 'houdini.py',
            data / 'hython',
            data / 'sitecustomize.py',
        ):
        with p.open('rb') as f:
            file_digest(f, lambda: self_hash)
    yield Path('SELF'), self_hash.digest()
    hash.update(self_hash.digest())
    yield Path('PROJECT'), hash.digest()


def checksum_project_dict() -> ChecksumMap:
    """
    Get the checksum of the project as a dictionary.
    """
    return {
        path: chksum.hex()
        for path, chksum in checksum_project()
        if path is not None
    }


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
def checksum_save_command() -> None:
    """
    Save the checksum of the project's configuration files to a file.
    """
    checksum_save()


def checksum_save() -> None:
    """
    Save the checksum of the project's configuration files to a file.
    """
    file = ZABOB_ROOT / '.checksums'
    with file.open('w') as out:
        write_checksums(out)


def read_checksums(in_: IO[str]|Path, /) -> ChecksumMap:
    """
    Read the checksums from a file.

    Args:
        in_ (IO[str]|Path): The file to read the checksums from.
    Returns:
        ChecksumMap: A dictionary of the checksums.
    """
    if isinstance(in_, Path):
        with in_.open('r') as f:
            return read_checksums(f)
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
def checksum_diff_command() -> set[Path]:
    """
    Compare the checksums of the project and its subprojects.

    Exits with 0 if the checksums are identical, 1 if they differ.
    """
    diff = checksum_diff()
    if diff:
        sys.exit(1)
    else:
        sys.exit(0)

def checksum_diff(old: ChecksumMap|None=None,
                  new: ChecksumMap|None=None) -> set[Path]:
    """
    Compare the checksums of the project and its subprojects.
    Returns:
        set[Path]: A set of subproject paths that have changed.
    """
    old = old or read_checksums(ZABOB_CHECKSUMS)
    new = new or checksum_project_dict()
    diff = diff_checksums(old, new)
    SELF = Path('SELF')
    projects: set[Path] = set()
    if diff.added or diff.removed or diff.changed:
        print("Checksums differ:")
        for path in sorted(diff.added, key=str):
            print(f"  + {path}")
            if path in ALLPROJECTS or path == SELF:
                projects.add(path)
        for path in sorted(diff.removed, key=str):
            print(f"  - {path}")
            if path in ALLPROJECTS or path == SELF:
                projects.add(path)
        for path in sorted(diff.changed, key=str):
            print(f"  ~ {path}")
            if path in ALLPROJECTS or path == SELF:
                projects.add(path)
        if projects:
            if SELF in projects:
                print('All projects need to be rebuilt due to changes in setup or checksum')
                return set(ALLPROJECTS)
            else:
                print("The following projects need to be rebuilt:")
                for project in sorted(projects, key=str):
                    print(f"  - {project}")
        return projects
    else:
        print("Checksums are identical.")
        return set()

@main.command()
@click.argument('name', type=click.Path(exists=False))
def find_up(name: str) -> None:
    """
    Find the path to a file in the project and output it to stdout.

    This can be evaluated in the shell simulate sourcing the script.

    The search terminates at:
    1) The first matching file found.
    2) The first directory that is not a subdirectory of the project root.
    3) The first directory that is not a subdirectory of the home directory.
    Args:
        name (str): The name of the file to find. This can be a relative path.
    """
    dir = Path.cwd()
    while True:
        path = dir / name
        if path.exists():
            import shutil
            with path.open('r') as f:
                # Copy the file to stdout
                shutil.copyfileobj(f, sys.stdout)
                return
        if dir == ZABOB_ROOT or dir == Path.home():
            break
        if (dir / '.gkt').exists():
            return
        if dir.parent == dir:
            return
        dir = dir.parent
    return None


type PathEdits = dict[str, list[str]]
'''
A dictionary of PATH-like variables and the values that should be added or removed.
'''
type EnvSettings = dict[str, str]
'''
Values to set in the environment.
'''
type EnvironmentUpdate = tuple[PathEdits, PathEdits, EnvSettings]
'''
A tuple of three dictionaries:
1. The PATH-like variables that had values added.
2. The PATH-like variables that had values removed.
3. The environment variables that were changed.

This is can be used to udate the environment variables in python, or to generate a script
to set the environment variables in the shell.
'''

@main.command()
@click.option('--shell',
              type=click.Choice(['bash', 'zsh', 'fish'], case_sensitive=False),
              default='bash',
              help="The shell to use. This should be the same as the one used to run the script.")
@click.option('--cwd', type=click.Path(exists=True, file_okay=False),
              default=Path.cwd(),
              help="The directory to run the script in.")
@click.option('--export/--no-export',
              default=True,
              help="Whether to export the variables or not.")
@click.argument('script')
def dump_source_env(script: str,
                    cwd: Path=Path.cwd(),
                    shell: Literal['bash', 'zsh', 'fish']='bash',
                    export: bool=True,
                    ) -> None:
    """
    dump_source_env [options] SCRIPT

    Dump the environment variables that are set by a script to be sourced.

    This can be evaluated in the shell to simulate sourcing the script
    but that just sets the environment variables.

    The variables should be dumped in the format:

    ```bash
        export VAR=value
        export PATH=...
    ```

    Lines that start with #, are blank, or begin with whitespace are ignored.
    Lines that do not fit the identifier=value format are ignored.
    Surrounding quotes are removed.

    Only values which are changed from the default are included.

    The [export] is optional.
    Args:
        file (Path): The file to dump the environment variables to.
    """
    shell = cast(Literal['bash', 'zsh', 'fish'], shell.lower())
    if shell == 'bash':
        noprofile = '--noprofile'
    elif shell == 'zsh':
        noprofile = '--no-rcs'
    elif shell == 'fish':
        noprofile = '--no-config'
    else:
        raise ValueError(f"Unknown shell: {shell}")
    script = shellquote(script)

    cmd =[shell, noprofile, '-c', f'source "{script}" && env']

    value = capture(*cmd,
                    #shell=True,
                    stdin=subprocess.DEVNULL,
                    cwd=cwd,
                    )
    if DEBUG.enabled:
        DEBUG(f"Script output: {value}")
    # We need to run the script in a subshell to get the environment variables
    for line in generate_env_script(*scrape_env(value),
                                    export=export):
        print(line)


@main.command(context_settings={"ignore_unknown_options": True})
@click.option('--cwd',
              type=click.Path(exists=True, file_okay=False),
              help="The directory to run the command in.")
@click.option('--assignment',
              default='=',
              help='The assignment operator used in the output. Usually "=", but hconfig uses " := ".')
@click.option('--export/--no-export',
              default=True,
              help="Whether to export the variables or not.")
@click.argument('cmd', nargs=-1)
def dump_env(cmd: list[str],
            cwd: Path=Path.cwd(),
            assignment: str='=',
            export: bool=True,
             ) -> None:
    """
    dump_env [options] CMD ARGS*


    Dump the environment variables that are set by a script to be sourced.

    This can be evaluated in the shell to simulate sourcing the script
    but that just sets the environment variables.

    The variables should be dumped in the format:

    ```bash
        export VAR=value
        export PATH=...
    ```

    An alternate assignment operator such as ":=" can be used
    via the --assignment option.

    Lines that start with #, are blank, or begin with whitespace are ignored.
    Lines that do not fit the identifier=value format are ignored.
    Surrounding quotes are removed.

    Only values which are changed from the default are included.

    The [export] is optional.
    Args:
        file (Path): The file to dump the environment variables to.
    """

    value = capture(*cmd,
                    shell=False,
                    cwd=cwd)
    for line in generate_env_script(*scrape_env(value, assignment=assignment),
                                    export=export):
        print(line)


def shellquote(value: str) -> str:
    """
    Quote a string for use in a shell command.
    This is used to escape special characters in the string.
    """
    if not value:
        return ''
    # No guarantee of security here, just avoiding the most common pitfalls.
    # Avoid the shell if injection attacks are a concern.
    value = value.replace("\\", '\\\\')
    value = value.replace('"', r'\"')
    value = value.replace("'", r"\'")
    value = value.replace('$', r'\$')
    value = value.replace('`', r'\`')
    value = value.replace('\n', r'\n')
    value = value.replace('\r', r'\r')
    value = value.replace('\t', r'\t')
    value = value.replace(' ', r'\ ')
    return value


def scrape_env(value: str,
               assignment: str='=') -> EnvironmentUpdate:
    '''
    Scrape the environment variables from a script or program.

    This computes the difference between the current environment and the
    environment after running the script or program.
    The output is in the format:

    ```bash
        export VAR=value
        export PATH=...
    ```
    Lines that start with #, are blank, or begin with whitespace are ignored.
    Lines that do not fit the identifier=value format are ignored.
    Surrounding quotes are removed.

    For PATH-like variables, the difference is computed between the
    current environment and the environment after running the script or program.
    The additions are returned as a list of strings in the first dictionary.
    The removals are returned as a list of strings in the second dictionary.
    The environment variables that were changed are returned as a dictionary

    Args:
        value (str): The output of the script or program.
    Returns:
        tuple[dict[str, list[str]], dict[str, list[str]], dict[str, str]]:
            A tuple of three dictionaries:
            1. The PATH-like variables that had values added.
            2. The PATH-like variables that had values removed.
            3. The environment variables that were changed.
    '''
    adds = {}
    removes = {}
    changes = {}
    for line in value.splitlines():
        line = line.strip()
        if line.startswith('export '):
            line = line[7:].lstrip()
        if not line or line.startswith('#'):
            continue
        if assignment not in line:
            continue
        name, value = line.split(assignment, 1)
        name = name.strip()
        value = value.strip()
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        elif value.startswith("'") and value.endswith("'"):
            value = value[1:-1]
        if name in ('VIRTUAL_ENV', 'VIRTUAL_ENV_PROMPT', '_', 'PWD'):
            # Ignore these variables, they are set by the virtualenv
            continue
        if name.endswith('PATH'):
            new = value.split(os.pathsep)
            old = os.environ.get(name, '').split(os.pathsep)
            add = set(new) - set(old)
            remove = set(old) - set(new)
            adds[name] = list(add)
            removes[name] = list(remove)
        elif value != os.environ.get(name, ''):
        # Stupid shell quoting rules.
            changes[name] = shellquote(value)
    return adds, removes, changes

def generate_env_script(
    adds: PathEdits,
    removes: PathEdits,
    changes: EnvSettings,
    /,
    export: bool=True,
    ) -> Generator[str, Any, None]:  # noqa: F821
    """
    Generate a script to set the environment variables.
    This can be used to set the environment variables in the current shell by using:

    ```bash
        eval "$(devtool setup --dump-env)"
    ```

    Args:
        adds (dict[str, list[str]]): The PATH-like variables that had values added.
        removes (dict[str, list[str]]): The PATH-like variables that had values removed.
        changes (dict[str, str]): The environment variables that were changed.
    Returns:
        str: The script to set the environment variables.
    """
    yield from _format_path_adds(adds, export=export)
    yield from _format_path_removes(removes, changes, export=export)
    yield from _format_path_changes(changes, export=export)

def _format_path_adds(adds: PathEdits, /,
                      export: bool=True,
                      ):
    """
    Format the path additions for use in a script.
    This is used to format the path additions for use in a script.
    """
    s = os.pathsep
    export_ = 'export ' if export else ''
    yield from (
        f'{export_}{name}="{s.join(values)}{s}${{{name}}}"'
        for name, values in adds.items()
    )

def _format_path_removes(removes: PathEdits, changes: EnvSettings, /,
                         export: bool=True,
                         ):
    """
    Format the path removals for use in a script.
    This is used to format the path removals for use in a script.
    """
    s = os.pathsep
    export_ = 'export ' if export else ''\

    L, R='${', '}'
    yield from (
        f'# remove "{v}" from {name}\n'
        f'{export_}{name}="{L}{name}/{s}{v}{s}/{s}{R}'
        for name, values in removes.items()
        for v in values
    )
    yield from (
        f'# Remove any trailing {s}\n'
        f'{export_}{name}="{L}{name}%{s}{R}"'
        for name, value in removes.items()
    )


def _format_path_changes(changes: EnvSettings, /,
                        export: bool=True,
                        ):
    """
    Format the path changes for use in a script.
    This is used to format the path changes for use in a script.
    """
    export_ = 'export ' if export else ''
    yield from (
        f'{export_}{name}="{value}"'
        for name, value in changes.items()
    )


if __name__ == '__main__':
    checksum_command()
