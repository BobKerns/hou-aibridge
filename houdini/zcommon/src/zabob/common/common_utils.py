'''
Common Utilities.
'''

from collections import defaultdict
from collections.abc import Callable, Generator, Iterable, MutableMapping
from operator import itemgetter
import os
from contextlib import contextmanager, suppress
from enum import Enum, StrEnum
import sys
from typing import IO, Hashable, Literal, TypeVar, Any
import atexit
from weakref import WeakKeyDictionary

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

_name_counter: MutableMapping[str, int] = defaultdict[str, int](lambda: 0)
_names: MutableMapping[Any, str] = WeakKeyDictionary[Any, str]()
def get_name(d: Any) -> str:
    '''
    Get the name of the given object. If it does not have a name,
    one will be assigned.

    If the object has a `name` or `__name__` attribute, it will
    be used as the name.

    If the object has a method called `name`, `getName`,
    or `get_name`, it will be called to try to get the name.

    Args:
        d (Any): The object to get the name of.
    Returns:
        str|None: The name of the object, or `None` if it has no name.
    '''
    match d:
        case Enum():
            return str(d.name)
        case str() | int() | float() | complex() | bool():
            return str(d)
        case None:
            return "None"
        case _ if hasattr(d, '__name__'):
            return str(d.__name__)
        case _ if hasattr(d, 'name') and isinstance(d.name, str):
            # If the object has a name attribute that is a string, return it.
            return str(d.name)
        case _ if hasattr(d, 'name') and callable(d.name):
            try:
                return str(d.name())
            except Exception:
                pass
        case _ if hasattr(d, 'get_name') and callable(d.get_name):
            try:
                return str(d.get_name())
            except Exception:
                pass
        case _ if hasattr(d, 'getName') and callable(d.getName):
            try:
                return str(d.get_name())
            except Exception:
                pass
        case _ if hasattr(d, 'name'):
            return str(d.name)
        case d if isinstance(d, Hashable):
            n = _names.get(d, None)
            if n is not None:
                return n
            pass
        case _:
            pass
    # If we reach here, we don't have a name, so generate one.
    typename = get_name(type(d))
    _name_counter[typename] += 1
    c = _name_counter[typename]
    n = f"{typename}_{c}"
    try:
        # If the object has a __name__ attribute, set it to the generated name.
        # This is useful for debugging and logging.
        setattr(d, '__name__', n)
        return n
    except AttributeError:
        if isinstance(d, Hashable):
           # If the object is hashable, store the name in a weak dictionary.
           _names[d] = n
           return n
        else:
           # If we can't save the name, generate one based on the id.
           return f"{typename}_{id(d):x}"

def do_all(i: Iterable):
    """
    Iterate over the items in the iterable (usually a `Generator`)
    and do nothing with them.

    This is useful for iterating over an iterable when you don't care about the
    items, but you want to ensure that the iterable is fully consumed.

    Args:
        i (Iterable): The iterable to iterate over.
    """
    for _ in i:
        pass
    # This is a no-op, but it ensures that the iterable is fully consumed.

def do_until(i: Iterable[T],
             condition: Callable[[T], bool]|None=None,
             default: R=None,
             ) -> T|R:
    """
    Iterate over the items in the iterable until the condition is met.

    If no item meets the condition, return the default value (default=None).

    `do_until` and `find_first` are the same function, but `do_until`
    emphasizes its use to perform actions via a generator.

    Args:
        i (Iterable[T]): The iterable to iterate over.
        condition (Callable[[T], bool]|None): The condition to check for each item.
            If None, all non-None items are considered to meet the condition.
        default (R): The default value to return if no item meets the condition.

    Returns:
        T: The first item that meets the condition,
        or R (the default value) if no item meets the condition.
    """
    if condition is None:
        return next((item
                     for item in i
                     if item is not None),
                    default)
    else:
        return next((item
                    for item in i
                    if condition(item)),
                default)

find_first = do_until

def do_while(i: Iterable[T],
             condition: Callable[[T], bool]|None=None,
             default: R=None,
             ) -> T|R:
    """
    Iterate over the items in the iterable until the condition is met.
    If no item meets the condition, return the default value (default=None).

    `do_while` and `find_first_not` are the same function, but `do_until`
    emphasizes its use to perform actions via a generator.

    Args:
        i (Iterable[T]): The iterable to iterate over.
        condition (Callable[[T], bool]|None): The condition to check for each item.
            If None, all non-None items are considered to meet the condition.
        default (R): The default value to return if all items meet the condition.
    Returns:
        T: The first item that does not the condition,
        or R (the default value) if all items meet the condition.
    """
    if condition is None:
        return next((item
                     for item in i
                     if item is None),
                    default)
    else:
        return next((item
                    for item in i
                    if not condition(item)),
                default)

find_first_not = do_while

def last(i: Iterable[T],
          condition: Callable[[T], bool],
          default: R=None,
          ) -> T|R:
    """
    Get the last item in the iterable that meets the condition.

    If no item meets the condition, return the default value (default=None).

    Unlike many implementations, this tests the entire iterable, ensuring
    that any generator is fully consumed before returning a value.
    """
    val: T = last # # type: ignore
    for item in i:
        if condition(item):
            val = item
    return val if val is not last else default

def trace(v: T,
          label: str|None=None,
          file:IO[str]=sys.stderr,
          condition: Callable[[T], bool]|None=None,
          ) -> T:
    '''
    Like print, but returns the value.
    This is useful for debugging, as it allows you to see the value
    while still returning it for further processing.

    Args:
        v (T): The value to trace.
        label (str|None): An optional label to print before the value.
        file (IO[str]): The file to print the trace to (default: sys.stderr).
        condition (Callable[[T], bool]|None): An optional condition to check
            before printing the value. If None, the value is always printed.
    Returns:
        T: The value that was traced.
    '''
    if condition is not None and condition(v):
        if label is not None:
            print(f"{label}: {v}", file=file)
        else:
            print(v, file=file)
    return v


def trace_(i: Iterable[T],
           label: str|None=None,
           file:IO[str] = sys.stderr,
           condition: Callable[[T], bool]|None=None,
           ) -> Iterable[T]:
    """
    Iterate over the items in the iterable and trace each item.
    This is useful for debugging, as it allows you to see the items
    while still returning them for further processing.

    Args:
        i (Iterable[T]): The iterable to iterate over.
        label (str|None): An optional label to print before each item.
        file (IO[str]): The file to print the trace to (default: sys.stderr).
        condition (Callable[[T], bool]|None): An optional condition to check
            before printing each item. If None, all items are printed.
    Yields:
        T: Each item in the iterable after tracing it.

    Returns:
        T: the returned items:
        or R (the default value) if no item meets the condition.
    """
    return (trace(item, label, file) for item in i)
