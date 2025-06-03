'''
Common Utilities.
'''

from collections.abc import Callable, Generator
import os
from contextlib import contextmanager, suppress
from enum import StrEnum
import sys
from typing import Literal, TypeVar
import atexit

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


@contextmanager
def prevent_exit():
    """Context manager that prevents sys.exit() from terminating the process."""
    original_exit = sys.exit

    def exit_handler(code=0):
        # Instead of exiting, raise a custom exception
        raise RuntimeError(f"Module attempted to exit with code {code}")

    # Replace sys.exit temporarily
    sys.exit = exit_handler
    try:
        yield
    finally:
        # Always restore the original exit function
        sys.exit = original_exit


@contextmanager
def prevent_atexit():
    """Temporarily prevent modules from registering atexit handlers."""
    original_register = atexit.register
    original_unregister = atexit.unregister
    captured_handlers = []

    def fake_register(func, *args, **kwargs):
        """Capture atexit handlers instead of registering them."""
        print(f"Prevented atexit registration: {func.__module__}.{func.__name__}")
        captured_handlers.append((func, args, kwargs))
        return func

    def fake_unregister(func):
        """Do nothing when unregistering."""
        pass

    # Replace the atexit functions
    atexit.register = fake_register
    atexit.unregister = fake_unregister

    try:
        yield
    finally:
        # Restore original functions
        atexit.register = original_register
        atexit.unregister = original_unregister


T = TypeVar('T')
R = TypeVar('R')
def none_or(value: T|None, fn: Callable[[T], R]) -> R|None:
    """
    Call a function with the given value if it is not None, otherwise return None.

    Args:
        value (T|None): The value to pass to the function.
        Callable[T]: The function to call with the value.

    Returns:
        R|None: The result of the function call or None if value is None.
    """
    if value is None:
        return None
    return fn(value)


def not_none(*values: T|None) -> Generator[T, None, None]:
    '''
    Generator that yields the values if they are not None.
    Args:
        *values (T|None): The values to yield.
    Yields:
        T: All non-None values from the arguments.
    '''
    for v in values:
        if v is not None:
            yield v


def not_none1(value: T|None) -> Generator[T, None, None]:
    '''
    Generator that yields the single value if it is not None.
    Args:
        value (T|None): The value to yield.
    Yields:
        T: The value if it is not None.
    '''
    if value is not None:
        yield value


def not_none2(value1: T|None, value2: T|None) -> Generator[T, None, None]:
    '''
    Generator that yields the single value if it is not None.
    Args:
        value1 (T|None): The first value to yield.
        value2 (T|None): The second value to yield.
    Yields:
        T: The first or second value if it is not None.
    '''
    if value1 is not None:
        yield value1
    if value2 is not None:
        yield value2


def values(*args: T) -> Generator[T, None, None]:
    """
    Generator that yields all the values from the given arguments.
    A substitute for a tuple that can be more clear about intent.

    Args:
        *args (T|None): The values to yield.

    Yields:
        T: All non-None values from the arguments.
    """
    for value in args:
        yield value

def if_true(condition: bool, value: T) -> Generator[T, None, None]:
    """
    Yield the value if the condition is True, otherwise return None.

    Args:
        condition (bool): The condition to check.
        value (T): The value to return if the condition is True.

    Yields:
        T|None: The value if the condition is True, otherwise None.
    """
    if condition:
        yield value

def if_false(condition: bool, value: T) -> Generator[T, None, None]:
    """
    Yield the value if the condition is False, otherwise return None.

    Args:
        condition (bool): The condition to check.
        value (T): The value to return if the condition is False.

    Yields:
        T|None: The value if the condition is False, otherwise None.
    """
    if not condition:
        yield value
