'''
Hython invoker
'''

import click
from zabob.main import main


@main.command(
    name='hython',
    help='Run hython with the given arguments.',
)
@click.argument(
    'arguments',
    type=str,
    help='Arguments to pass to hython.',
)
def hython(arguments: list[str]):
    """
    Run hython with the given arguments.
    """
    import subprocess
    import sys

    # Check if hython is installed
    try:
        subprocess.run(['hython', '--version'], check=True)
    except FileNotFoundError:
        print("Hython is not installed. Please install it first.")
        sys.exit(1)

    # Run hython with the given arguments
    subprocess.run(['hython', *arguments])
