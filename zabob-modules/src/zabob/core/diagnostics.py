'''
Diagnostic tools.
'''

from click import group

from zabob.common import check_environment

@group("diagnostics")
def diagnostics():
    """Diagnostic tools for Zabob."""
    pass

diagnostics.add_command(check_environment)
