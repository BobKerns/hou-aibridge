'''
Support for the `devtools update` command line tool.
'''

from collections.abc import Collection
from os import PathLike
from pathlib import Path
import sys
from typing import cast
import click
from semver import Version
import tomlkit
import tomlkit.container
from tomlkit.toml_file import TOMLFile

from devtool_modules.utils import needs_update, VERBOSE
from devtool_modules.main import main, sync_dependencies
from devtool_modules.paths import IMAGES_DIR, PROJECT_ROOT
from devtool_modules.subproc import run

@main.group(name='update')
def update() -> None:
    """
    <CMD> Operations that update the project.
    Use the --help option for more information on a specific command.
    """
    pass


@update.group('all')
def update_all() -> None:
    """
    <CMD> Operations that update an entire set of files.
    Use the --help option for more information on a specific command.

    Example:
      devtool update all diagrams
    """
    pass

@update_all.command(name='release')
def run_all():
    "Run all commands in preparation for release."
    update_diagrams()
    sync_dependencies()
    update_version()


BACKGROUND_COLOR = 'fdf2e4'
DIAGRAMS: list[tuple[Path, *tuple[str,...]]] = [
        (IMAGES_DIR / 'compiler_classes.mmd', '-t', 'default', '--backgroundColor', BACKGROUND_COLOR, '-s', '1'),
        (IMAGES_DIR / 'input_classes.mmd', '-t', 'default', '--backgroundColor', BACKGROUND_COLOR, '-s', '1'),
        (IMAGES_DIR / 'erDiagram.mmd', '-t', 'default', '--backgroundColor', BACKGROUND_COLOR, '-s', '1'),
        (IMAGES_DIR / 'erDiagramUserSubset.mmd', '-t', 'default', '--backgroundColor', BACKGROUND_COLOR, '-s', '1'),
        (IMAGES_DIR / 'erDiagramGeometry.mmd', '-t', 'default', '--backgroundColor', BACKGROUND_COLOR, '-s', '1'),
]

@update.command(name='diagram')
@click.argument('diagram', type=click.Path(exists=True))
@click.option('--png', is_flag=True, help="Generate a PNG file instead of an SVG file.")
def update_diagram_command(diagram: PathLike|str, png: bool=False) -> None:
    "[<PATH>] Update the given diagram."
    try:
        update_diagram(diagram, png=png)
    except* Exception as e:
        for exc in e.exceptions:
            print(f"Failed to update diagram: {exc}", file=sys.stderr)
        sys.exit(1)
    print("Diagram updated successfully.")
    sys.exit(0)


def update_diagram(diagram: PathLike|str, *params: str,
                   png: bool=False) -> None:
    "<PATH> Update the given diagram."
    diagram = Path(diagram).resolve()
    fmt = '.svg'
    if png:
        fmt = '.png'
    if not params:
        diagram_spec = next((d for d in DIAGRAMS if d[0] == diagram), None)
        if diagram_spec is None:
            print(f"Diagram {diagram} not found in the list of diagrams, using defaults", file=sys.stderr)
            params = ('-t', 'default', '--backgroundColor', BACKGROUND_COLOR, '-s', '1')
        else:
            params = diagram_spec[1:]

    infile = PROJECT_ROOT / diagram
    outfile = infile.with_suffix(fmt)
    if not infile.exists():
        raise FileNotFoundError(f"Diagram {diagram} not found.")
    VERBOSE(f"Updating {diagram}...")
    try:
        run('npx', 'mmdc', '-i', infile, '-o', outfile, *params)
    except Exception as e:
        raise RuntimeError(f"Failed to update {diagram}: {e}.") from e


@update_all.command(name='diagrams')
@click.option('--force', is_flag=True, help="Force update all diagrams.")
@click.option('--suffixes',
              type=click.STRING,
              default='.svg',
              help="Comma-separated list of suffixes.")
def update_diagrams_command(force: bool=False, suffixes: str='') -> None:
    "Update all diagrams."
    try:
        VERBOSE(f"Updating diagrams with suffixes {suffixes}...")
        suffixes_ = [
            s2
            for s2 in (
                s.strip()
                for s in suffixes.split(',')
            )
            if s2
        ]
        update_diagrams(suffixes=suffixes_, force=force)

    except* Exception as e:
        for exc in e.exceptions:
            print(f"Failed to update diagrams: {exc}", file=sys.stderr)
        sys.exit(1)
    print("Diagrams updated successfully.")
    sys.exit(0)


def update_diagrams(suffixes: Collection[str]=('.svg'),
                    force: bool=False,
                    ) -> None:
    '''
    Update all diagrams, collecting errors into a single ExceptionGroup.

    Parameters:
        suffixes (Collection[str]): A collection of suffixes to check for.
        force (bool): If True, force update all diagrams, even if they are up to date.
    '''
    def replace_suffix(f: PathLike|str, suffix: str) -> Path:
        "Replace the suffix of a file, but add more to the stem."
        f = Path(f)
        f = f.with_suffix('')
        return f.with_name(f.stem + suffix)
    excs = []
    for diagram, *params in DIAGRAMS:
        try:
            files =[
                                replace_suffix(diagram, suffix)
                                for suffix in suffixes
                            ]
            if force or needs_update(diagram, *files):
                update_diagram(diagram, *params)

        except Exception as e:
            excs.append(e)
    if excs:
        raise ExceptionGroup("Failed to update some diagrams", excs)

@update.command(name='version')
def update_version() -> None:
    "Update the version in the pyproject.toml file."

    pyproject = PROJECT_ROOT / 'pyproject.toml'
    if not pyproject.exists():
        raise FileNotFoundError("pyproject.toml not found.")
    file = TOMLFile(pyproject)
    toml = file.read()
    project = cast(tomlkit.container.Container, toml['project'])
    version = Version.parse(str(project['version']))
    version = version.bump_patch()
    project['version'] = str(version)
    print(f"Updating version to {version}...")
    file.write(toml)


