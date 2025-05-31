'''
Common Utilities.
'''

import os
from contextlib import contextmanager, suppress
from enum import StrEnum
from typing import Literal

from semver import Version


def _version(version: Version|str) -> Version:
    """
    Convert a version to a semver.Version object.

    Args:
        version (Version|str): The version to convert.

    Returns:
        Version: The converted version.
    """
    if isinstance(version, Version):
        return version
    return Version.parse(version, optional_minor_and_patch=True)


class Level(StrEnum):
    """
    Enum for logging levels. Each level acts both as a string and as a callable.

    Calling `INFO("message")` will print the message if the current logging level
    is `INFO` or more verbose. The levels are ordered from most verbose to least
    verbose. The default level is `INFO`. `DEBUG` will print all messages, while
    `SILENT` will suppress all output except for explicit calls to `SILENT`.
    """
    DEBUG = "DEBUG"
    VERBOSE = "VERBOSE"
    INFO = "INFO"
    QUIET = "QUIET"
    SILENT = "SILENT"

    level: 'Level'

    @property
    def enabled(self) -> bool:
        """
        Check if the current logging level is enabled.
        """
        return LEVELS.index(self) >= LEVELS.index(Level.level)

    def __call__(self, message: str) -> None:
        """
        Output a message at the specified logging level.
        """
        if self.enabled:
            # Only print the message if the current logging level is
            # at least as verbose as the message level.
            print(message)


Level.level = Level.INFO

LEVELS: tuple[Level, ...] = tuple(Level.__members__.values())
'''
Ordered list of logging levels, fro the most verbose to the least verbose.
'''

DEBUG: Literal[Level.DEBUG]= Level.DEBUG
VERBOSE: Literal[Level.VERBOSE] = Level.VERBOSE
INFO: Literal[Level.INFO] = Level.INFO
QUIET: Literal[Level.QUIET] = Level.QUIET
SILENT: Literal[Level.SILENT] = Level.SILENT

@contextmanager
def environment(*remove, **update):
    """
    Temporarily updates the ``os.environ`` dictionary in-place.

    The ``os.environ`` dictionary is updated in-place so that the modification
    is sure to work in all situations.

    :param remove: Environment variables to remove.
    :param update: Dictionary of environment variables and values to add/update.
    """
    env = os.environ
    update = update or {}
    remove = remove or []

    # List of environment variables being updated or removed.
    stomped = (set(update.keys()) | set(remove)) & set(env.keys())
    # Environment variables and values to restore on exit.
    update_after = {k: env[k] for k in stomped}
    # Environment variables and values to remove on exit.
    remove_after = frozenset(k for k in update if k not in env)

    try:
        env.update(update)
        for k in remove:
            with suppress(KeyError):
                del env[k]
        yield
    finally:
        env.update(update_after)
        for k in remove_after:
            with suppress(KeyError):
                del env[k]
