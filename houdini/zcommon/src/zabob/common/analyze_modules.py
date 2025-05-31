'''
Analyze the modules that are available in the current Houdini environment.
'''


import builtins
from collections.abc import Container, Generator, Sequence
from dataclasses import dataclass
from enum import Enum, StrEnum
from importlib import import_module
from inspect import getdoc, getmembers, isclass, isdatadescriptor, isfunction, ismethod, ismethoddescriptor, ismodule
from pathlib import Path
import sqlite3
import sys
from types import ModuleType
from typing import Any

from semver import Version

from zabob.common.common_paths import ZABOB_HOUDINI_DATA
from zabob.common.common_utils import environment
from zabob.common.timer import timer


def import_or_warn(module_name: str):
    """
    Import a module and warn if it fails.
    Args:
        module_name (str): The name of the module to import.
    Returns:
        module: The imported module, or None if the import failed.
    """
    try:
        with environment(HOUDINI_ENABLE_HOM_EXTENSIONS='1',):
            print(f"Importing {module_name}...")
            yield import_module(module_name)
    except Exception as e:
        print(f"Warning: Failed to import {module_name}: {e}", file=sys.stderr)


class EntryType(StrEnum):
    """
    Enum for entry types in the Houdini static data.
    """
    MODULE = 'module'
    CLASS = 'class'
    FUNCTION = 'function'
    METHOD = 'method'
    ENUM = 'enum'
    CONSTANT = 'constant'
    OBJECT = 'object'
    ATTRIBUTE = 'attribute'
    ENUM_TYPE = 'EnumType'


@dataclass
class HoudiniStaticData:
    """
    A class to represent static data extracted from Houdini 20.5.

    Attributes:
        name (str): The name of the Houdini item (module, class, function, etc.).
        type (str): The type of the Houdini item (e.g., 'module', 'class', 'function', 'constant', etc.).
        datatype (str): The data type of the Houdini item (e.g., 'int', 'str', 'hou.EnumValue', etc.).
        docstring (str|None): The docstring of the Houdini item, or None if not available.
        parent_name (str|None): The name of the parent Houdini item, if applicable.
        parent_type (str|None): The type of the parent Houdini item, if applicable.
    """
    name: str
    type: EntryType
    datatype: builtins.type
    docstring: str|None = None
    parent_name: str|None = None
    parent_type: str|None = None

@dataclass
class ModuleData:
    """
    A class to represent module data extracted from Houdini 20.5.

    Attributes:
        name (str): The name of the module.
        file (Path): The file path of the module.
    """
    name: str
    file: Path|None


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


def get_static_module_data(include: Sequence[ModuleType], ignore: Container[str]) -> Generator[HoudiniStaticData|ModuleData, Any, None]:
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
    seen = set()
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
        if module.__name__ in ignore:
            return
        file = getattr(module, '__file__', None)
        name = module.__name__
        if file is not None:
            file = Path(file).resolve()
        yield ModuleData(name, file)
        module_data = mk_datum(module, EntryType.MODULE,
                               parent,
                               name=name)
        yield module_data
        for member_name, member in get_members_safe(module):
            if member_name.startswith('_'):
                continue
            if ismodule(member) or isinstance(member, ModuleType):
                yield from load_module(member,
                                       parent=module_data)
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

            if ismodule(member):
                yield from load_module(member,
                                       parent=class_data)
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
        yield from load_module(module)

def get_static_data_db_path(out_dir: Path=ZABOB_HOUDINI_DATA) -> Path:
    """
    Get the path to the static data database for a specific Houdini version.

    Args:
        out_dir (Path): The output directory parent where the database will be stored.

    Returns:
        The path to the static data database for the specified Houdini version.
    """
    version = Version.parse(*hou.applicationVersion())
    outpath = out_dir / str(version) / 'houdini_static_data.db'
    outpath.parent.mkdir(parents=True, exist_ok=True)
    return outpath


def save_static_data_to_db(db_path: Path|None=None,
                           out_dir: Path=ZABOB_HOUDINI_DATA,
                           connection: sqlite3.Connection|None=None,
                           include: Sequence[ModuleType] = (),
                           ignore: Container[str] = ()
                        ):
    """
    Save the static data to a SQLite database.

    Args:
        db_path (str): The path to the SQLite database file.
    """
    def save(conn: sqlite3.Connection):
        """
        Save the static data to the database.
        Args:
            conn (sqlite3.Connection): The SQLite connection to use.
        """
        cursor = conn.cursor()
        print('Initializing tables...')
        cursor.execute('PRAGMA foreign_keys = ON;')
        # Create tables if they doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS houdini_module_data (
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                datatype TEXT NOT NULL,
                docstring TEXT,
                parent_name TEXT DEFAULT NULL,
                parent_type TEXT DEFAULT NULL,
                PRIMARY KEY (name, type) ON CONFLICT REPLACE,
                FOREIGN KEY (parent_name, parent_type) REFERENCES houdini_static_data(name, type)
            ) STRICT
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS houdini_modules (
                name TEXT NOT NULL PRIMARY KEY,
                file TEXT DEFAULT NULL
            ) STRICT
        ''')

        with timer('Storing') as progress:
            # Insert or update static data
            for datum in get_static_module_data(include, ignore):
                if isinstance(datum, ModuleData):
                    conn.commit()
                    progress(f'Processing module {datum.name}...')
                    cursor.execute('''
                        INSERT OR REPLACE INTO houdini_static_modules (name, file)
                        VALUES (?, ?)
                    ''', (datum.name, str(datum.file) if datum.file else None))
                else:
                    def name(d: Any) -> str:
                        if isinstance(d, Enum):
                            return str(d)
                        if isinstance(d, str):
                            return str(d)
                        n = getattr(d, 'name', None)
                        if callable(n):
                            try:
                               n = n()
                            except Exception:
                                n = None
                        if n is not None:
                            return str(n)
                        return (
                            getattr(d, '__name__', None)
                            or str(d)
                        )

                    if datum.parent_name is not None:
                        #print(f'Processing {datum.type} {datum.name} with parent {datum.parent_name}...')
                        #if str(name) == 'BlendShape' or name == 'hou' or datum.type == EntryType.OBJECT:
                        #    breakpoint()
                        cursor.execute('''
                            INSERT OR REPLACE INTO houdini_static_data (name, type, datatype, docstring,
                                                                        parent_name, parent_type)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (
                            datum.name, name(datum.type), name(datum.datatype), datum.docstring,
                            datum.parent_name, name(datum.parent_type)))
                    else:
                        #print(f'Processing {datum.type} {datum.name} without parent...')
                        cursor.execute('PRAGMA foreign_keys = OFF;')
                        conn.commit()
                        cursor.execute('''
                            INSERT OR REPLACE INTO houdini_static_data (name, type, datatype, docstring, parent_name, parent_type)
                            VALUES (?, ?, ?, ?, NULL, NULL)
                        ''', (datum.name, name(datum.type), name(datum.datatype), datum.docstring))
                        cursor.execute('PRAGMA foreign_keys = ON;')
                        conn.commit()

        # Commit last module.
        conn.commit()

        # Vacuum the database to optimize it. Most of the time this is not needed,
        # but if reloading the tables during development, it shows the actual space needed.
        with timer('Vacuuming database'):
            cursor.execute('''
            VACUUM;
            ''')
    if connection is not None:
        save(connection)
    else:
        if db_path is None:
            db_path = get_static_data_db_path(out_dir)
        print(f'Saving static data to {db_path}...')
        with sqlite3.connect(db_path) as conn:
            save(conn)
    print(f'static module data saved to {db_path}.')
