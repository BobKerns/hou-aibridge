'''
Commands relating to Houdini
'''

from devtools.houdini_versions import cli as houdini_cli
from devtools.main import main

@main.group('houdini')
def houdini_commands():
    """
    Houdini commands.
    """
    pass


for name, command in houdini_cli.commands.items():
    # Register the command with the main group
    houdini_commands.add_command(command, name)

    # Add the command to the Houdini commands gr
