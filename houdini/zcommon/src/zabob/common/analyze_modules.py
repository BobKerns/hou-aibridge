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
a status of the `Exception` that was raised, and a reason being the message of the `Exception`.

If the import is rejected, it yields a `ModuleData` object with the name of the module,
the file it was found in, a status of `'IGNORE'`, and a reason being the value from the
`ignore` mapping.

If module name has already been processed, it is skipped; nothing is yielded for it.

If the import succeeds, it yields a `ModuleData` object with the name of the module,
the file and directory (or `None` if not available), and a status of `None` This indicts that
the module was successfully imported its analysis will follow. A status of `'OK'` is set
in the database only after all items in the module have been processed, as failure can
occur at any point during the analysis. Failures during analysis will result in another
`ModuleData` object being yielded with the status set to the `Exception` that was raised,
and a reason being the message of the `Exception`. This allows the database to record the
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
a successful import, the status is set to `'OK'` and the count of items in the the module
is saved. The counter is then reset to zero, as the next module will be processed.

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
from contextlib import suppress, chdir
from enum import Enum
from importlib import import_module
from inspect import (
    getdoc, getmembers, isclass, isdatadescriptor, isfunction,
    ismethod, ismethoddescriptor, ismodule,
)
from pathlib import Path
import sys
from types import ModuleType
from typing import Any
import warnings
from collections import deque
from tempfile import TemporaryDirectory
import inspect


from zabob.common.infinite_mock import InfiniteMock
from zabob.common.analysis_types import (
    EntryType, HoudiniStaticData, ModuleData, AnalysisFunctionSignature, ParameterSpec
)
from zabob.common.common_paths import ZABOB_ROOT
from zabob.common.common_utils import (
    VERBOSE, environment, get_name, prevent_atexit, prevent_exit, none_or, values
)
from zabob.common.timer import timer
from zabob.common.overload_collector import (
    collect_overloads, get_overload_for_function, remove_overload_info
)


def reject(m: ModuleType|ModuleData,
            seen: set[ModuleType],
            done: set[str],
            ignore: Mapping[str, str],
             file: Path|None,
             ):
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
    for name in reject_name(m.__name__, done, ignore, file):
        seen.add(m)
        yield m


def reject_name(name: str,
                done: set[str],
                ignore: Mapping[str, str],
                file: Path|None) -> Generator[str|ModuleData, None, None]:
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

def modules_in_path(path: Sequence[str|Path],
                    seen: set[ModuleType]|None=None,
                    done: set[str]|None=None,
                    ignore: Mapping[str, str]| None = None,
                    ) -> Generator[ModuleType|ModuleData, None, None]:
    """
    Import modules from the given path.
    Args:
        path (Sequence[str|Path]): A sequence of paths to import modules from.
        ignore (Container[str]): A container of module names to ignore.
        done: (Iterable[str]): An iterable of module names that have already been processed.
    Yields:
        ModuleType: The imported module.
    """
    seen = seen or set()
    done = done or set()
    ignore = ignore or {}
    paths = (Path(p) for p in path)

    # A step at a time, go from candidate module name + file, to either
    # the module itself, or a ModuleData object describing why it was rejected.
    yield from (m
        for p in paths
        for candidate, file in candidates_in_dir(p)
        for name in reject_name(candidate, done, ignore, file)
        for mod in import_or_warn(name)
        for m in reject(mod, seen, done, ignore,  file)
    )
    # Do a final pass over sys.modules
    yield from (m
                for mod in sys.modules.values()
                for file in values (getattr(mod, '__file__', None),)
                for m in reject(mod,
                                seen=seen,
                                done=done,
                                ignore=ignore,
                                file=none_or(file, Path) )
    )


def candidates_in_dir(path: Path) -> Generator[tuple[str, Path], None, None]:
    """
    Generate candidate module names from a directory path.

    `Path` -> `str` (module name).
    Args:
        path (Path): The directory path to search for modules.
    Yields:
        str: The candidate module name.
        Path: The file path of the module.
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
                    VERBOSE(f"Importing {module_name}...")
                    with collect_overloads():
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


_hou_initialized: bool = False
def _init_hou() -> ModuleType:
    """
    Initialize the hou module and its submodules, mocking them if necessary.
    This function ensures that the hou module and its submodules are available
    and mocks what can be mocked to maximize what modules can be analyzed.

    Returns:
        ModuleType: The initialized hou module.
    """
    global _hou_initialized
    import hou
    if _hou_initialized:
        # Already initialized, return the hou module.
        return hou
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
    _hou_initialized = True
    return hou


def _docstring(v):
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
    hou = _init_hou()
    return (isinstance(v, type)
            and any(isinstance(m, hou.EnumValue)
                    for n, m in get_members_safe(v)
                    if not n.startswith('_')
                    if not n == 'thisown')
            and all(isinstance(m, hou.EnumValue)
                    for n, m in get_members_safe(hou.primType)
                    if not n.startswith('_')
                    if n != 'thisown'))


builtin_function_or_method = type(builtins.repr)

def _dtype(v) -> builtins.type:
    '''
    Get the data type of a Houdini object, mapping tuple types to `tuple`
    for easier understanding.
    '''
    t = type(v)
    name = t.__name__
    if 'tuple' in name or 'Tuple' in name:
        return tuple
    return t



def _mk_datum(item: Any, type: EntryType, parent: HoudiniStaticData|None=None, name: str|None=None) -> HoudiniStaticData:
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
    datatype = _dtype(item)
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
        docstring=_docstring(item),
        parent_name=parent.name if parent else None,
        parent_type=parent.type if parent else None
    )

def _convert_signature_to_params(sig: inspect.Signature) -> list[ParameterSpec]:
    """
    Convert an inspect.Signature object to a list of ParameterSpec dictionaries.
    """
    params = []
    for name, param in sig.parameters.items():
        param_spec: ParameterSpec = {
            'name': name,
            'type': get_name(param.annotation) if param.annotation is not inspect.Parameter.empty else 'Any',
            'kind': get_name(param.kind).split('.')[-1],  # Extract name from enum
        }

        if param.default is not inspect.Parameter.empty:
            param_spec['default'] = str(param.default)
            param_spec['is_optional'] = True

        params.append(param_spec)
    return params

def _yield_function_signatures(module_name: str, func_name: str,
                              parent_data: HoudiniStaticData,
                              func_obj: Any | None = None) -> Generator[AnalysisFunctionSignature, None, None]:
    """
    Check for and yield function signature information.

    Args:
        module_name: Base module name
        func_name: Fully qualified function name (including parent classes)
        parent_data: Parent data for creating signature entries
        func_obj: The actual function object (preferred for accurate lookup)

    Yields:
        AnalysisFunctionSignature instances for both implementations and overloads if found
    """
    # Add debug logging
    print(f"DEBUG: Looking for overloads of {module_name}.{func_name}")

    # Always try to create a signature from the function object first
    # This ensures we get a signature even if there's no overload info
    simple_func_name = func_name.split('.')[-1]
    signature_created = False

    # Check for overload information first
    overload_info = get_overload_for_function(module_name=module_name, func_name=func_name)

    if overload_info:
        print(f"DEBUG: Found overload info with {len(overload_info.signatures)} signatures")

        # Create entries for each overload signature
        for i, sig_info in enumerate(overload_info.signatures):
            if sig_info.signature:
                params = _convert_signature_to_params(sig_info.signature)
                return_type = str(sig_info.type_hints.get('return', 'Any'))

                yield AnalysisFunctionSignature(
                    func_name=simple_func_name,
                    parameters=params,
                    return_type=return_type,
                    is_overload=True,
                    overload_index=i+1,
                    file_path=sig_info.file_path,
                    line_number=sig_info.line_number,
                    parent_name=parent_data.name,
                    parent_type=parent_data.type
                )
                print(f"DEBUG: Created overload signature #{i+1} for {simple_func_name}")

        # If there's an implementation, add that too
        if overload_info.implementation and overload_info.implementation.signature:
            impl = overload_info.implementation
            params = _convert_signature_to_params(impl.signature)
            return_type = str(impl.type_hints.get('return', 'Any'))

            yield AnalysisFunctionSignature(
                func_name=simple_func_name,
                parameters=params,
                return_type=return_type,
                is_overload=False,
                file_path=impl.file_path,
                line_number=impl.line_number,
                parent_name=parent_data.name,
                parent_type=parent_data.type
            )
            print(f"DEBUG: Created implementation signature for {simple_func_name} from overload info")
            signature_created = True

        # Clean up after processing
        remove_overload_info(module_name, func_name)
    else:
        print(f"DEBUG: No overload info found for {module_name}.{func_name}")

    # If we haven't created a signature from overloads, try to create one from the function object
    if not signature_created and func_obj is not None:
        try:
            sig = inspect.signature(func_obj)
            print(f"DEBUG: Successfully inspected signature: {sig}")

            params = _convert_signature_to_params(sig)

            # Try to get return type hint if available
            return_type = "Any"
            try:
                from typing import get_type_hints
                type_hints = get_type_hints(func_obj)
                if 'return' in type_hints:
                    return_type = str(type_hints['return'])
            except Exception as e:
                print(f"DEBUG: Error getting type hints: {e}")

            yield AnalysisFunctionSignature(
                func_name=simple_func_name,
                parameters=params,
                return_type=return_type,
                is_overload=False,
                file_path=None,  # We don't have this info for direct inspection
                line_number=None,
                parent_name=parent_data.name,
                parent_type=parent_data.type
            )
            print(f"DEBUG: Created signature for {simple_func_name} from direct inspection")

        except Exception as e:
            print(f"DEBUG: Failed to inspect function directly: {e}")

def _load_class(cls, parent: HoudiniStaticData,
                seen: set[str],
                queue: deque[tuple[HoudiniStaticData, ModuleType]],
                queued: set[ModuleType],
                name: str|None=None,
                ) -> Generator[HoudiniStaticData|ModuleData|AnalysisFunctionSignature, None, None]:
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
    hou = _init_hou()
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
    class_data = _mk_datum(cls, type, parent)
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
            if member not in seen and member not in queued:
               queue.append((class_data, member))
               queued.add(member)
        elif isclass(member):
            yield from _load_class(member,
                                    parent=class_data,
                                    seen=seen,
                                    queue=queue,
                                    queued=queued,
                                    name=f'{name}.{member_name}')
        elif isinstance(member, property):
            yield _mk_datum(member, EntryType.ATTRIBUTE,
                            parent=class_data,
                            name=member_name)
        else:
            member_data = _mk_datum(member, type,
                            parent=class_data,
                            name=member_name)
            yield member_data

            # Check for overloads after yielding the function/method
            if type in (EntryType.METHOD, EntryType.FUNCTION):
                # For methods, use the full qualified name to ensure uniqueness
                qualified_name = f"{cls.__module__}.{cls.__name__}.{member_name}"
                # Pass the base module name and fully qualified function name
                yield from _yield_function_signatures(cls.__module__, qualified_name, member_data, member)

def _load_module(module,
                seen: set[Any],
                done: set[str],
                ignore: Mapping[str, str],
                queue: deque[tuple[HoudiniStaticData, ModuleType]],
                queued: set[ModuleType],
                parent: HoudiniStaticData|None=None,
                top: bool = True,
                ) -> Generator[HoudiniStaticData|ModuleData|AnalysisFunctionSignature, None, None]:
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
    module_data = _mk_datum(module, EntryType.MODULE,
                            parent,
                            name=name)
    yield module_data
    hou = _init_hou()
    for member_name, member in get_members_safe(module):
        if member_name.startswith('_'):
            continue
        if ismodule(member) and not isinstance(member, InfiniteMock):
            if not member in seen and member not in queued:
                queue.append((module_data, member))
                queued.add(member)
        elif isclass(member):
            yield from _load_class(member,
                                    parent=module_data,
                                    seen=seen,
                                    queue=queue,
                                    queued=queued,)
        elif isfunction(member):
            func_data = _mk_datum(member, EntryType.FUNCTION,
                            parent=module_data,
                            name=member_name)
            yield func_data

            # Check for overloads after yielding the function
            qualified_name = f"{module.__name__}.{member_name}"
            yield from _yield_function_signatures(module.__name__, qualified_name, func_data, member)
        elif isinstance(member, (Enum, hou.EnumValue)):
            yield _mk_datum(member, EntryType.ENUM,
                            parent=module_data,
                            name=member_name)
        elif (
            ismethod(member)
            or ismethoddescriptor(member)
            or isinstance(member, builtin_function_or_method)
        ):
            func_data = _mk_datum(member, EntryType.FUNCTION,
                            parent=module_data,
                            name=member_name)
            yield func_data

            # Check for overloads after yielding the function
            qualified_name = f"{module.__name__}.{member_name}"
            yield from _yield_function_signatures(module.__name__, qualified_name, func_data, member)
        else:
            yield _mk_datum(member, EntryType.OBJECT,
                            parent=module_data,
                            name=member_name)
    if top:
        while len(queue) > 0:
            # Process the queue until it's empty.
            # This ensures that modules are processed in the order they were found,
            # and that module/items alternation is preserved.
            parent_data, module = queue.popleft()
            # Process the next module in the queue.
            yield from _load_module(module,
                                seen=seen,
                                done=done,
                                ignore=ignore,
                                queue=queue,
                                queued=queued,
                                parent=parent_data,
                                top=False,
                                )


def analyze_modules(include: Iterable[ModuleType|ModuleData],
                    ignore: Mapping[str, str]|None = None,
                    done: Iterable[str]= (),
                    ) -> Generator[HoudiniStaticData|ModuleData|AnalysisFunctionSignature, Any, None]:
    """
    Extract static data from Houdini 20.5 regarding modules, classes, functions, and constants
    etc. exposed by the hou module.

    This function traverses the hou module and its submodules, collecting information
    about each item, including its name, type, data type, docstring, Houdini version,
    and parent information if applicable.

    Yields:
        HoudiniStaticData: An instance of HoudiniStaticData for each item found in the hou module.
        ModuleData: An instance of ModuleData for each module found in the hou module.
    """

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
    queued = set()
    '''
    A set of modules which have ever been queued for processing. We only need them queued once.
    '''

    with TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        tmpdir.chmod(0o500)
        # We need a read-only working directory to catch modules which try to write to the filesystem.
        with chdir(tmpdir):
            for module in include:
                if not isinstance(module, ModuleType):
                    # If it's already a ModuleData, yield it directly.
                    yield module
                else:
                    yield from _load_module(module,
                                            seen=set(),
                                            done=set(done),
                                            ignore=ignore or {},
                                            queue=queue,
                                            queued=queued,
                                            )

