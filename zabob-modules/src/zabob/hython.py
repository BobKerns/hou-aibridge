'''
Hython invoker
'''

import click
from zabob.find_houdini import get_houdini
from zabob.main import main


@main.command(
    name='hython',
    help='Run hython with the given arguments.',
    context_settings=dict(
        ignore_unknown_options=True,
    )
)
@click.argument(
    'arguments',
    nargs=-1,
    type=str,
)
def hython(arguments: list[str]):
    """
    Run hython with the given arguments.
    """
    import subprocess
    import sys

    # Check if hython is installed
    houdini = get_houdini()
    if houdini is None:
        print("Houdini is not installed or not found.")
        sys.exit(1)
    hython_path = houdini.hython
    try:
        subprocess.run([hython_path, '--version'], check=True)
    except FileNotFoundError:
        print("Hython is not installed. Please install it first.")
        sys.exit(1)

    # Run hython with the given arguments
    subprocess.run(['hython', *arguments])
