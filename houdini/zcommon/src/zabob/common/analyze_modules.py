'''
Analyze the modules that are available in the current Houdini environment.

This is a streaming architecture based on nested generators.

Conceptually, it starts with a list of strings yielded from `sys.path`, which are
turned into `Path` objects, which are scanned for directories representing
python packages, and files which potentially represent python modules. Apparent
packages have their component module file `Path` objects yielded first, followed by
the package directory itself. This is done to ensure that the package directory
is always yielded after its components.

The next layer attempts to import these modules. If the import fails, it yields
a `ModuleData` object with the name of the module, the file and directory it was found in,
a status of the Exception that was raised, and a reason being the message of the Exception.

If the import is rejected, it yields a `ModuleData` object with the name of the module,
the file it was found in, a status of 'IGNORE', and a reason being the value from the
`ignore` mapping.

If module name has already been processed, it is skipped; nothing is yielded for it.

If the import succeeds, it yields a `ModuleData` object with the name of the module,
the file and directory (or None if not available), and a status of None This indicts that
the module was successfully imported its analysis will follow. A status of 'OK' is set
in the database only after all items in the module have been processed, as failure can
occur at any point during the analysis. Failures during analysis will result in another
`ModuleData` object being yielded with the status set to the Exception that was raised,
and a reason being the message of the Exception. This allows the database to record the
failure without losing the module's name and file information, and retaining the partial
results of the analysis.

If the module is a package, it is traversed recursively, yielding `HoudiniStaticData` objects,
which contain the name, type, data type, docstring, parent name and parent type of the item.
The items are classified as modules, classes, functions, methods, enums, constants, attributes,
objects, and enum types. The parent information is included if the item is a member of a class
or module. Modules encountered at any point are recursed into after the other members are
processed, to avoid intermixing data from different modules, so the module/items alternation
preserved.

The database handler receives this alternation of `ModuleData` and `HoudiniStaticData`.
The information in the `ModuleData` is added to the `houdini_modules` table. If it is
a successful import, the count of items in the the module is set to zero.

The `HoudiniStaticData` objects are then added to the `houdini_module_data` table.

When the next module (or failure of the current module) is encountered, the previous
module's data is updated with the count and status.

The amount or storage used at any one time is minimal, except for the cumulative loading
of modules. The loading process can be stopped at any time, and picked up in another process.
This allows for parallel processing of modules, though the amount of parallelism is determined
by the underlying database.

It also allows the to be resumed after a failure, or to be partitioned to limit the amount of
memory from loaded modules at nny one time.

It also allows for analysis of additional modules that were not present initially, as when the
user installs additional packages or modules after the initial analysis.

'''


import builtins
from collections.abc import Generator, Iterable, Mapping, Sequence
from contextlib import suppress
from dataclasses import dataclass
from enum import Enum, StrEnum
from importlib import import_module
from inspect import (
    getdoc, getmembers, isclass, isdatadescriptor, isfunction,
    ismethod, ismethoddescriptor, ismodule,
)
from pathlib import Path
import sys
from types import ModuleType
from typing import Any, Literal
import warnings
from collections import deque

import sqlite3

from zabob.common.infinite_mock import InfiniteMock
from zabob.common.analysis_db import analysis_db, analysis_db_writer, get_stored_modules
from zabob.common.analysis_types import EntryType, HoudiniStaticData, ModuleData
from zabob.common.common_paths import ZABOB_ROOT
from zabob.common.common_utils import (
    do_all, environment, get_name, prevent_atexit, prevent_exit, none_or, values
)
from zabob.common.timer import timer

def modules_in_path(path: Sequence[str|Path],
                    ignore: Mapping[str, str]|None=None,
                    done: Iterable[str]=()) -> Generator[ModuleType|ModuleData, None, None]:
    """
    Import modules from the given path.
    Args:
        path (Sequence[str|Path]): A sequence of paths to import modules from.
        ignore (Container[str]): A container of module names to ignore.
        done: (Iterable[str]): An iterable of module names that have already been processed.
    Yields:
        ModuleType: The imported module.
    """
    ignore = ignore or {}
    paths = (Path(p) for p in path)
    seen: set[ModuleType] = set()
    done = set(done)
    def reject(m: ModuleType|ModuleData, file: Path|None):
        """
        Check if the module is a duplicate.
        Args:
            m (ModuleType|ModuleData): The module or `ModuleData` to check.
        Yields:
            ModuleData if the module is rejected, otherwise the module itself.
        """
        if isinstance(m, ModuleData):
            # Already rejected module, pass it along.
            yield m
            return
        if m in seen:
            # Duplicate module, skip it.
            return
        if not ismodule(m) or isinstance(m, InfiniteMock):
            # Not a module, skip it.
            return
        file = none_or(getattr(m, '__file__', file), Path)
        for name in reject_name(m.__name__, file):
            seen.add(m)
            yield m

    def reject_name(name: str, file: Path|None) -> Generator[str|ModuleData, None, None]:
        """
        Check if the module is a duplicate.
        Args:
            name (str): The module name to check.
        Returns:
            bool: True if the module is rejected, False otherwise.
        """
        if name in done:
            # Already seen this module, skip it.
            return
        if name.startswith('zabob.'):
            # Zabob modules are not to be imported here.
            return
        if name in ignore:
            yield ModuleData(name=name, file=file, status='IGNORE', reason=ignore[name])
        else:
            yield name

    # A step at a time, go from candidate module name + file, to either
    # the module itself, or a ModuleData object describing why it was rejected.
    yield from (m
        for p in paths
        for candidate, file in candidates_in_dir(p)
        for name in reject_name(candidate, file)
        for mod in import_or_warn(name)
        for m in reject(mod, file)
    )
    # Do a final pass over sys.modules
    yield from (m
                for mod in sys.modules.values()
                for file in values (getattr(mod, '__file__', None),)
                for m in reject(mod, none_or(file, Path) )
    )


def candidates_in_dir(path: Path) -> Generator[tuple[str, Path], None, None]:
    """
    Generate candidate module names from a directory path.

    `Path` -> `str` (module name).
    Args:
        path (Path): The directory path to search for modules.
    Yields:
        str: The candidate module name.
    """
    if not path.is_dir():
        return
    if ZABOB_ROOT in path.parents:
        # If the path is inside the zabob root, skip it.
        return
    for item in path.iterdir():
        if item.is_file() and item.suffix == '.py':
            yield (item.stem, item)
        if item.name in ('test', 'site-packages', 'site-packages-forced'):
            continue
        elif item.is_dir() and (item / '__init__.py').exists():
            yield from (
                (item.name + '.' + subitem.stem, subitem)
                for subitem in item.iterdir()
                if subitem.is_file() and subitem.suffix == '.py'
                and subitem.name != '__init__.py'
                and subitem.name != '__main__.py'
            )
            # Finally, the parent.
            yield (item.name, item)
        elif item.is_dir():
            # If it's a directory without __init__.py, it may still be a namespace package.
            yield from (
                (f'{item.name}.{pkg.stem}.{subitem.stem}', subitem)
                for pkg in (pkgdir
                            for pkgdir in item.iterdir()
                            if pkgdir.is_dir() and (pkgdir / '__init__.py').exists())
                for subitem in pkg.iterdir()
                if subitem.is_file() and subitem.suffix == '.py'
                if subitem.name != '__init__.py'
                if subitem.name != '__main__.py'
            )
            yield from (
                (f'{item.name}.{pkg.stem}', pkg)
                for pkg in (pkgdir
                            for pkgdir in item.iterdir()
                            if pkgdir.is_dir() and (pkgdir / '__init__.py').exists())
            )

def import_or_warn(module_name: str|ModuleData, file: Path|None=None) -> Generator[ModuleType|ModuleData, None, None]:
    """
    Import a module and warn if it fails.
    Args:
        module_name (str): The name of the module to import.
        file (Path|None): The file path of the module, if available.
    Yields:
        module: The imported module, or a `ModuleData` if the import failed.
    """
    if not isinstance(module_name, str):
        # If it's already a ModuleData, yield it directly.
        yield module_name
        return
    # Protect against modules that try to exit the interpreter
    try:
        with environment(HOUDINI_ENABLE_HOM_EXTENSIONS='1'):
            with prevent_exit():
                with prevent_atexit():
                    print(f"Importing {module_name}...")
                    with warnings.catch_warnings():
                        warnings.filterwarnings('ignore',
                                                message='pyside_type_init:_resolve_value',
                                                category=RuntimeWarning)
                        warnings.simplefilter('ignore', DeprecationWarning)
                        module = import_module(module_name)
                        if ismodule(module):
                            yield module
                        else:
                            raise TypeError(f"{module_name} is not a module, skipping")
    except Exception as e:
        if "attempted to exit" in str(e):
            print(f"Warning: Module {module_name} attempted to exit, skipping", file=sys.stderr)
        else:
            print(f"Warning: Failed to import {module_name}: {e}", file=sys.stderr)
        yield ModuleData(name=module_name, file=file, status=e)


def get_members_safe(obj: Any):
    """
    Safely get members of an object, excluding private members.
    Args:
        obj (Any): The object to get members from.
    yields:
        tuple[str, Any]: A tuple containing the name and member of the object.
    """
    try:
        yield from getmembers(obj)
    except Exception as e:
        print(f"Warning: Failed to get members of {obj}: {e}", file=sys.stderr)


def get_static_module_data(include: Iterable[ModuleType|ModuleData],
                           ignore: Mapping[str, str],
                           done: Iterable[str]
        ) -> Generator[HoudiniStaticData|ModuleData, Any, None]:
    """
    Extract static data from Houdini 20.5 regarding modules, classes, functions, and constants
    etc. exposed by the hou module.

    This function traverses the hou module and its submodules, collecting information
    about each item, including its name, type, data type, docstring, Houdini version,
    and parent information if applicable.

    Yields:
        HoudiniStaticData: An instance of HoudiniStaticData for each item found in the hou module.
        ModuleData: An instance of ModuleData for each module found in the hou module.
    The data includes:


    Returns:
        dict: A dictionary containing the static data.
    """
    import hou
    if getattr(hou, 'ui', None) is None:
        hou.ui = InfiniteMock(hou, 'hou.ui')
    if getattr(hou, 'qt', None) is None:
        hou.qt = InfiniteMock(hou, 'hou.qt')
    if getattr(hou, 'viewportVisualizers', None) is None:
        hou.viewportVisualizers = InfiniteMock(hou, 'hou.viewportVisualizers')
    sys.modules['hdefereval'] = InfiniteMock(hou, 'hou.hdefereval') # type: ignore[assignment]
    with suppress(Exception):
        import hutils.PySide # type: ignore[import]
        sys.modules['hutil.PySide.Qt'] = hutils.PySide = InfiniteMock(hou, 'hutils.PySide.Qt') # type: ignore[assignment]
        sys.modules['hutil.PySide.QTGui'] = hutil.PySide.QtGui = InfiniteMock(hou, 'hutils.PySide.QtGui') # type: ignore[assignment]
        sys.modules['hutil.PySide.QtActions'] = hutil.PySide.QtActions = InfiniteMock(hou, 'hutils.PySide.QtActions') # type: ignore[assignment]
        sys.modules['hutil.PySide.QtWidgets'] = hutils.PySide.QtWidgets = InfiniteMock(hou, 'hutils.PySide.QtWidgets') # type: ignore[assignment]
        sys.modules['hutil.PySide.QtCore'] = hutils.PySide.QtCore = InfiniteMock(hou, 'hutils.PySide.QtCore') # type: ignore[assignment]
        sys.modules['hutil.Qt'] = hutils.Qt = InfiniteMock(hou, 'hutils.Qt') # type: ignore[assignment]
        sys.modules['hutil.Qt.QtGui'] = hutils.Qt.QtGui = InfiniteMock(hou, 'hutils.Qt.QtGui') # type: ignore[assignment]
        sys.modules['hutil.Qt.QtWidgets'] = hutils.Qt.QtWidgets = InfiniteMock(hou, 'hutils.Qt.QtWidgets') # type: ignore[assignment]
        sys.modules['hutil.Qt.QtCore'] = hutils.Qt.QtCore = InfiniteMock(hou, 'hutils.Qt.QtCore') # type: ignore[assignment]
    with suppress(Exception):
        import PySide # type: ignore[import]
        sys.modules['PySide.Qt'] = PySide = InfiniteMock(hou, 'PySide2.Qt') # type: ignore[assignment]
        sys.modules['PySide.QTGui'] = PySide.QtGui = InfiniteMock(hou, 'PySide.QtGui') # type: ignore[assignment]
        sys.modules['PySide.QtActions'] = PySide.QtActions = InfiniteMock(hou, 'PySide.QtActions') # type: ignore[assignment]
        sys.modules['PySide.QtWidgets'] = PySide.QtWidgets = InfiniteMock(hou, 'PySide.QtWidgets') # type: ignore[assignment]
        sys.modules['PySide.QtCore'] = PySide.QtCore = InfiniteMock(hou, 'PySide.QtCore') # type: ignore[assignment]
    with suppress(Exception):
        import PySide2 # type: ignore[import]
        sys.modules['PySide2.Qt'] = PySide2 = InfiniteMock(hou, 'PySide2.Qt') # type: ignore[assignment]
        sys.modules['PySide2.QTGui'] = PySide2.QtGui = InfiniteMock(hou, 'PySide2.QtGui') # type: ignore[assignment]
        sys.modules['PySide2.QtActions'] = PySide2.QtActions = InfiniteMock(hou, 'PySide2.QtActions') # type: ignore[assignment]
        sys.modules['PySide2.QtWidgets'] = PySide2.QtWidgets = InfiniteMock(hou, 'PySide2.QtWidgets') # type: ignore[assignment]
        sys.modules['PySide2.QtCore'] = PySide2.QtCore = InfiniteMock(hou, 'PySide2.QtCore') # type: ignore[assignment]
    seen = set(done)
    builtin_function_or_method = type(builtins.repr)
    def dtype(v) -> builtins.type:
        t = type(v)
        name = t.__name__
        if 'tuple' in name or 'Tuple' in name:
            return tuple
        return t

    def docstring(v):
        """
        Get the docstring of a Houdini object, excluding the parent class docstring if it matches.
        Args:
            v (Any): The Houdini object to get the docstring for.
        Returns:
            str|None: The docstring of the object, or None if it is the same as the parent class docstring.
        """
        own = getdoc(v)
        if own is None:
            return None
        parent = getdoc(type(v))
        if own == parent:
            return None
        return getdoc(v) or None

    def ishouenumtype(v):
        """
        Check if the given value is a Houdini enum type.
        Args:
            v (Any): The value to check.
        Returns:
            bool: True if the value is a Houdini enum type, False otherwise.
        """
        return (isinstance(v, type)
                and any(isinstance(m, hou.EnumValue)
                        for n, m in get_members_safe(v)
                        if not n.startswith('_')
                        if not n == 'thisown')
                and all(isinstance(m, hou.EnumValue)
                        for n, m in get_members_safe(hou.primType)
                        if not n.startswith('_')
                        if n != 'thisown'))

    def mk_datum(item: Any, type: EntryType, parent: HoudiniStaticData|None=None, name: str|None=None) -> HoudiniStaticData:
        """
        Create a HoudiniStaticData instance.

        Args:
            item (Any): The item to create a HoudiniStaticData instance for.
            type (EntryType): The type of the item (e.g., 'module', 'class', 'function', 'constant', etc.).
            parent (HoudiniStaticData|None): The parent HoudiniStaticData instance, if any.
            name (str|None): The name of the item. If not provided, it will be derived from the item.
        Returns:
            HoudiniStaticData: An instance of HoudiniStaticData with the item's details.
        """
        name = name or getattr(item, '__name__', None) or str(item)
        assert name is not None, f"Item {item} has no name."
        datatype = dtype(item)
        if type == 'function' and parent and parent.type == 'class':
            type = EntryType.METHOD
        if name == 'EnumValue':
            type = EntryType.CLASS
        elif datatype == 'EnumValue':
            type = EntryType.ENUM
            datatype = parent.datatype if parent else datatype
        return HoudiniStaticData(
            name=name,
            type=type,
            datatype=datatype,
            docstring=docstring(item),
            parent_name=parent.name if parent else None,
            parent_type=parent.type if parent else None
        )

    queue: deque[tuple[HoudiniStaticData, ModuleType]] = deque()
    '''
    A queue to hold the modules to be processed. Holds tuples of (`HoudiniStaticData`, `ModuleType`),
    where the `HoudiniStaticData` is the the parent module data, and the `ModuleType` is the module
    to be processed.  This is essentially breadth-first traversal of the module tree.

    This serves ensure the module/items alternation is preserved, so that the backend can count
    and track the items in each module, and close off the module with its final status when all items
    have been processed. The database could be replaced with a report generator and generate a report
    without nesting of modules and items.

    This isn't strictly necessary.
    '''

    def load_module(module, parent: HoudiniStaticData|None=None) ->Generator[HoudiniStaticData|ModuleData, None, None]:
        """
        Load a module and its members, yielding HoudiniStaticData instances for each item.
        Args:
            module (module): The module to load.
            parent (HoudiniStaticData|None): The parent HoudiniStaticData instance, if any.
        Yields:
            HoudiniStaticData: An instance of HoudiniStaticData for each item found in the module (including the module).
            ModuleData: An instance of ModuleData for the module itself.
        """
        if module in seen:
            return
        seen.add(module)
        if module.__name__ in done:
            # Been here, done that.
            return
        file = none_or(getattr(module, '__file__', None), Path)
        if file is not None:
            file = file.resolve()
        if module.__name__ in ignore:
            name = module.__name__
            yield ModuleData(name=name,
                            file=file,
                            count=None,
                            status='IGNORE',
                            reason=ignore[name])
            return
        name = module.__name__
        yield ModuleData(name, file=file)
        module_data = mk_datum(module, EntryType.MODULE,
                               parent,
                               name=name)
        yield module_data
        for member_name, member in get_members_safe(module):
            if member_name.startswith('_'):
                continue
            if ismodule(member) and not isinstance(member, InfiniteMock):
                queue.append((module_data, member))
            elif isclass(member):
                yield from load_class(member,
                                      parent=module_data)
            elif isfunction(member):
                yield mk_datum(member, EntryType.FUNCTION,
                               parent=module_data,
                               name=member_name)
            elif isinstance(member, (Enum, hou.EnumValue)):
                yield mk_datum(member, EntryType.ENUM,
                               parent=module_data,
                               name=member_name)
            elif (
                ismethod(member)
                or ismethoddescriptor(member)
                or isinstance(member, builtin_function_or_method)
            ):
                # Extracted directly from a module, it's just another callable.
                yield mk_datum(member, EntryType.FUNCTION,
                               parent=module_data,
                               name=member_name)
            else:
                yield mk_datum(member, EntryType.OBJECT,
                               parent=module_data,
                               name=member_name)

        while len(queue) > 0:
            # Process the queue until it's empty.
            # This ensures that modules are processed in the order they were found,
            # and that module/items alternation is preserved.
            parent_data, module = queue.popleft()
            # Process the next module in the queue.
            yield from load_module(module, parent=parent_data)

    def load_class(cls, parent: HoudiniStaticData,
                   name: str|None=None
                   ) ->Generator[HoudiniStaticData|ModuleData, None, None]:
        """
        Load class members and their static data.
        Args:
            cls (type): The class to load.
            parent (HoudiniStaticData): The parent HoudiniStaticData instance.
        Yields:
            HoudiniStaticData: An instance of HoudiniStaticData for each class member found.
        """
        if cls in seen:
            return
        seen.add(cls)
        name = name or cls.__name__
        if name.startswith('_'):
            return
        type = EntryType.CLASS
        if cls is hou.EnumValue:
            type = EntryType.CLASS
        if issubclass(cls, (Enum, hou.EnumValue)):
            type = EntryType.ENUM
        elif ishouenumtype(cls):
            type = EntryType.ENUM_TYPE
        class_data = mk_datum(cls, type, parent)
        yield class_data
        for member_name, member in get_members_safe(cls):
            if member_name.startswith('_'):
                continue
            match member:
                case _ if ismethod(member):
                    type = EntryType.METHOD
                case _ if (isfunction(member)
                           or ismethoddescriptor(member)
                           or isinstance(member, builtin_function_or_method)
                ):
                    if parent.type == EntryType.CLASS:
                        type = EntryType.METHOD
                    else:
                        type = EntryType.FUNCTION
                case _ if isdatadescriptor(member):
                    type = EntryType.ATTRIBUTE
                case _ if isclass(member):
                    type = EntryType.CLASS
                case _:
                    type = EntryType.OBJECT
            if name.startswith('_'):
                    continue

            if ismodule(member) and not isinstance(member, InfiniteMock):
                queue.append((class_data, member))
            elif isclass(member):
                yield from load_class(member,
                                      parent=class_data,
                                      name=f'{name}.{member_name}')
            elif isinstance(member, property):
                yield mk_datum(member, EntryType.ATTRIBUTE,
                               parent=class_data,
                               name=member_name)
            else:
                yield mk_datum(member, type,
                               parent=class_data,
                               name=member_name)
    for module in include:
        if not isinstance(module, ModuleType):
            # If it's already a ModuleData, yield it directly.
            yield module
        else:
            yield from load_module(module)


def save_static_data_to_db(db_path: Path|None=None,
                           connection: sqlite3.Connection|None=None,
                           include: Iterable[ModuleType|ModuleData] = (),
                           ignore: Mapping[str, str]|None =None
                        ):
    """
    Save the static data to a SQLite database. Either a DB path or an existing connection must be provided.
    This function initializes the database tables if they do not exist, and then

    Args:
        db_path (Path|None): The path to the SQLite database file.
        connection (sqlite3.Connection|None): An existing SQLite connection, if available.
        include (Iterable[ModuleType|ModuleData]): An iterable of modules to include in the static data.
        ignore (Mapping[str, str]|None): A mapping of module names to ignore, with reasons.
    """
    ignore = ignore or {}
    with analysis_db(db_path=db_path,
                     connection=connection,
                     write=True) as conn:
        with analysis_db_writer(connection=conn) as writer:
            with timer('Storing') as progress:
                # Insert or update static data
                item_count = 0
                cur_module: ModuleData|None = None
                for datum in get_static_module_data(include=include,
                                                    ignore=ignore,
                                                    done=get_stored_modules(connection=conn)):
                    do_all(writer(datum))

        # Commit last module.
        conn.commit()

        # Vacuum the database to optimize it. Most of the time this is not needed,
        # but if reloading the tables during development, it shows the actual space needed.
        conn.execute('''
        VACUUM;
        ''')
