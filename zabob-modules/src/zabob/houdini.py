'''
Commands relating to Houdini
'''

from zabob.houdini_versions import cli as houdini_cli
from zabob.main import main

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
