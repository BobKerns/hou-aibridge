"""
Collects function overload information by monkey-patching the typing.overload decorator.
"""

from collections.abc import Iterator
import inspect
import sys
import types
import warnings
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, get_type_hints
from inspect import Parameter, Signature
from pathlib import Path

# Define a fallback signature for uninspectable functions
FALLBACK_SIGNATURE = Signature(
    parameters=[
        Parameter('args', Parameter.VAR_POSITIONAL),
        Parameter('kwargs', Parameter.VAR_KEYWORD)
    ],
    return_annotation=Any
)
FALLBACK_TYPE_HINTS = {'return': Any}

@dataclass
class OverloadSignature:
    """Information about a single overload signature."""
    func_name: str
    module: str
    signature: inspect.Signature
    type_hints: dict[str, Any]
    line_number: int | None = None
    file_path: str | None = None

@dataclass
class OverloadInfo:
    """Collection of overload signatures for a function."""
    func_name: str
    module: str
    signatures: list[OverloadSignature] = field(default_factory=list)
    implementation: OverloadSignature | None = None

# Global registry of overloaded functions
overload_registry: dict[tuple[str, str], OverloadInfo] = {}

# Set to track modules we've already processed
processed_modules: set[str] = set()

# Store the original overload decorator
original_overload = None
is_active = False

def safe_get_type_hints(func):
    """
    Safely extract type hints from a function, handling common errors.

    Returns a dictionary of type hints or an empty dict if extraction fails.
    """
    try:
        return get_type_hints(func)
    except (NameError, TypeError, AttributeError):
        # Handle known issues with various packages
        # - NameError: Common with Literal, SchemaType, or other undefined names
        # - TypeError: Can happen with invalid annotations
        # - AttributeError: Can occur with complex descriptors

        # Fall back to examining __annotations__ directly
        hints = {}
        if hasattr(func, "__annotations__"):
            # Store annotations as strings to avoid evaluation errors
            for name, annotation in func.__annotations__.items():
                if isinstance(annotation, str):
                    hints[name] = annotation
                else:
                    # For non-string annotations, store their repr
                    try:
                        hints[name] = repr(annotation)
                    except Exception:
                        hints[name] = "Unknown"
        return hints

def capture_overload(func):
    """
    Replacement for typing.overload decorator that captures overload information.
    """
    global overload_registry

    # Only capture if collection is active
    if is_active:
        # Get information about the function
        module_name = func.__module__
        func_name = func.__qualname__
        key = (module_name, func_name)

        # Add debug logging
        print(f"DEBUG: Capturing overload for {module_name}.{func_name}")

        # Create frame info to get file and line number
        cur_frame = inspect.currentframe()
        assert cur_frame is not None, "Current frame should not be None in CPython"
        frame = cur_frame.f_back
        file_path = frame.f_code.co_filename if frame else None
        line_number = frame.f_lineno if frame else None

        # Store the overload info
        if key not in overload_registry:
            overload_registry[key] = OverloadInfo(func_name=func_name, module=module_name)

        # Create signature info
        try:
            sig = inspect.signature(func)
            type_hints = safe_get_type_hints(func)
        except (ValueError, TypeError):
            # For uninspectable functions, use the fallback signature
            sig = FALLBACK_SIGNATURE
            type_hints = FALLBACK_TYPE_HINTS

        overload_registry[key].signatures.append(
            OverloadSignature(
                func_name=func_name,
                module=module_name,
                signature=sig,
                type_hints=type_hints,
                line_number=line_number,
                file_path=file_path
            )
        )

        # Add more debug information
        print(f"DEBUG: Added overload signature to registry, now has {len(overload_registry[key].signatures)} signatures")

    # Call the original overload decorator to maintain normal typing behavior
    if original_overload:
        return original_overload(func)
    return func

def monkey_patch_overload():
    """
    Replace the typing.overload decorator with our capturing version.
    """
    global original_overload

    import typing

    # Save the original decorator
    if original_overload is None:
        original_overload = typing.overload

        # Replace with our version
        typing.overload = capture_overload

def capture_implementation(func):
    """
    Capture the implementation function that follows overloaded declarations.

    Returns the function unchanged, but may update the registry with implementation info.
    """
    if not is_active:
        return func

    module_name = func.__module__
    func_name = func.__qualname__
    key = (module_name, func_name)

    if key in overload_registry:
        # This looks like it might be an implementation of overloaded functions
        try:
            sig = inspect.signature(func)
            type_hints = safe_get_type_hints(func)
        except (ValueError, TypeError):
            # For uninspectable functions, use the fallback signature
            sig = FALLBACK_SIGNATURE
            type_hints = FALLBACK_TYPE_HINTS

        # Create frame info
        cur_frame = inspect.currentframe()
        assert cur_frame is not None, "Current frame should not be None in CPython"
        frame = cur_frame.f_back
        file_path = frame.f_code.co_filename if frame else None
        line_number = frame.f_lineno if frame else None

        # Add implementation to the registry
        overload_registry[key].implementation = OverloadSignature(
            func_name=func_name,
            module=module_name,
            signature=sig,
            type_hints=type_hints,
            line_number=line_number,
            file_path=file_path
        )

        # The registry is checked and yielded in the collect_overloads context manager

    return func

def reload_module_safely(module_name: str) -> bool:
    """
    Attempt to safely reload a module to capture its overloads.
    Returns True if successful, False otherwise.

    WARNING: This is an experimental feature that may cause system instability.
    """
    if module_name not in sys.modules:
        return False

    import importlib.util
    # Skip modules that are known to be unsafe to reload
    unsafe_modules = {
        # Core Python modules that should never be reloaded
        'sys', 'os', 'builtins', 'types', 'importlib', '_thread',
        # Modules with singletons or global state
        'logging', 'threading', 'multiprocessing',
        # Houdini-specific modules that might have C extensions
        'hou', 'hdefereval',
    }

    if module_name in unsafe_modules or module_name.startswith(('_', 'zabob.')):
        return False

    try:
        original_module = sys.modules[module_name]

        # Skip C extension modules which can't be reloaded
        if not hasattr(original_module, '__file__') or not isinstance(original_module.__file__, str):
            return False

        # Skip modules without a valid file path
        module_path = Path(original_module.__file__)
        if not module_path.exists():
            return False

        # Skip modules that aren't Python files
        if module_path.suffix.lower() not in ('.py', '.pyw'):
            return False

        # Temporarily remove from sys.modules and reload
        temp_copy = sys.modules.pop(module_name)
        try:
            # Use import machinery directly to avoid import hooks
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if spec is None or spec.loader is None:
                return False

            new_module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = new_module

            # This will execute the module code
            spec.loader.exec_module(new_module)

            # Now we've captured any overloads in the module
            return True
        finally:
            # Always restore the original module
            sys.modules[module_name] = temp_copy
    except Exception as e:
        # Any exception means we failed
        return False

# Add the missing function to skip problematic modules
def skip_problematic_modules():
    """
    Add known problematic modules to the processed_modules set to skip them.
    """
    global processed_modules

    # Modules known to cause issues with type hint collection
    problematic_modules = {
        # Modules with Literal not defined errors
        'requests', 'urllib', 'urllib3',
        # Modules with SchemaType errors
        'marshmallow', 'dataclasses_json',
        # Other modules that might cause issues
        'typing_extensions',  # Can have circular references
    }

    processed_modules.update(problematic_modules)

    # Also skip submodules of problematic packages
    for module_name in list(sys.modules.keys()):
        if any(module_name == prob_mod or module_name.startswith(f"{prob_mod}.")
               for prob_mod in problematic_modules):
            processed_modules.add(module_name)

@contextmanager
def experimental_module_reloader(modules_to_try: list[str] | None = None):
    """
    Experimental context manager that temporarily reloads specified modules to capture overloads.

    WARNING: This is highly experimental and may cause system instability or crashes.

    Args:
        modules_to_try: List of module names to try reloading. If None, uses a built-in safe list.

    Example:
        with experimental_module_reloader(['my.safe.module']):
            pass  # Overloads from the reloaded modules will be collected
    """
    if not is_active:
        warnings.warn("Overload collection is not active, module reloading will have no effect")
        yield
        return

    # Default to a relatively safe set of modules
    if modules_to_try is None:
        # These are modules that commonly contain overloads and might be safer to reload
        modules_to_try = [
            'typing', 'collections', 'functools', 'itertools',
            'pathlib', 'datetime', 'contextlib'
        ]

    warnings.warn(
        "Experimental module reloading is active. This may cause system instability.",
        RuntimeWarning, stacklevel=2
    )

    reloaded_count = 0
    try:
        for module_name in modules_to_try:
            if reload_module_safely(module_name):
                reloaded_count += 1

        yield
    finally:
        if reloaded_count:
            print(f"Experimentally reloaded {reloaded_count} modules to capture overloads")

def scan_loaded_modules(try_reload: bool = False, module_patterns: list[str] | None = None):
    """
    Scan already loaded modules for overloaded functions.

    Args:
        try_reload: If True, attempt experimental reloading of selected modules.
                   WARNING: This is highly experimental and may cause system instability.
        module_patterns: List of module name patterns to limit scanning to.
                        Each pattern can use '*' as a wildcard.
    """
    global processed_modules

    if not is_active:
        return

    # Handle experimental reloading if requested
    if try_reload and module_patterns:
        modules_to_try = []
        for pattern in module_patterns:
            if '*' in pattern:
                # Convert glob pattern to regex for matching
                import re
                regex = re.compile(pattern.replace('.', r'\.').replace('*', r'.*'))
                for module_name in sys.modules:
                    if regex.match(module_name) and module_name not in processed_modules:
                        modules_to_try.append(module_name)
            elif pattern in sys.modules and pattern not in processed_modules:
                modules_to_try.append(pattern)

        with experimental_module_reloader(modules_to_try):
            # Process any modules reloaded by the experimental reloader
            for key, info in list(overload_registry.items()):
                if info.implementation is not None:
                    yield info
                    del overload_registry[key]

    # Regular scanning of loaded modules
    for module_name, module in list(sys.modules.items()):
        if module_name in processed_modules or not isinstance(module, types.ModuleType):
            continue

        # If patterns are specified, check if this module matches any
        if module_patterns:
            import fnmatch
            if not any(fnmatch.fnmatch(module_name, pattern) for pattern in module_patterns):
                continue

        processed_modules.add(module_name)

        # Look for functions in the module
        for name, obj in inspect.getmembers(module):
            if inspect.isfunction(obj):
                # Check if this might be an implementation of overloaded functions
                capture_implementation(obj)

        # Yield any completed overloads from this module
        for key, info in list(overload_registry.items()):
            if info.implementation is not None:
                yield info
                del overload_registry[key]

def get_overload_info() -> dict[tuple[str, str], OverloadInfo]:
    """
    Return all collected overload information.
    """
    # Get remaining overloads after scanning
    for _ in scan_loaded_modules():
        pass  # Process any yielded items
    return overload_registry

def clear_registry():
    """
    Clear the collected overload information.
    """
    global overload_registry, processed_modules
    overload_registry = {}
    processed_modules = set()

def initialize():
    """
    Initialize the overload collector by monkey-patching.
    This doesn't activate collection yet.
    """
    monkey_patch_overload()

# Add a function to get a more precise function identifier
def get_function_key(func_obj: Any | None = None, module_name: str | None = None, func_name: str | None = None) -> tuple[str, str]:
    """
    Get a unique key for a function that properly handles class methods.
    Can work with either a function object or module_name/func_name strings.

    Returns:
        A tuple of (module_name, fully_qualified_name) to use as a lookup key
    """
    # Try to get information from func_obj if provided
    if func_obj is not None:
        # Try to get module name from func_obj, fall back to provided module_name
        obj_module = getattr(func_obj, '__module__', None)
        if obj_module is not None:
            module_name = obj_module

        # Try to get the function name from qualname (preferred) or name
        if hasattr(func_obj, '__qualname__'):
            func_name = func_obj.__qualname__
        elif hasattr(func_obj, '__name__'):
            func_name = func_obj.__name__
        # If we couldn't get a name, we'll fall back to the provided func_name

    # Ensure we have module_name and func_name
    if not module_name or not func_name:
        raise ValueError("Either function object with required attributes or module_name/func_name must be provided")

    # Construct the fully qualified name
    if not func_name.startswith(f"{module_name}."):
        fully_qualified_name = f"{module_name}.{func_name}"
    else:
        fully_qualified_name = func_name

    return (module_name, fully_qualified_name)

# Update the get_overload_for_function to use this
def get_overload_for_function(module_name: str | None = None, func_name: str | None = None,
                             func_obj: Any | None = None) -> OverloadInfo | None:
    """
    Get overload information for a specific function if available.

    Args:
        module_name: Name of the module containing the function
        func_name: Name of the function (may include class qualification)
        func_obj: The actual function object (preferred if available)

    Returns:
        OverloadInfo if the function has overloads, None otherwise
    """
    try:
        key = get_function_key(func_obj, module_name, func_name)
        return overload_registry.get(key)
    except ValueError:
        # If we can't get a key, return None
        return None

def remove_overload_info(module_name: str | None = None, func_name: str | None = None,
                        func_obj: Any | None = None) -> None:
    """
    Remove overload information for a specific function after it's been processed.

    Args:
        module_name: Name of the module containing the function
        func_name: Name of the function (may include class qualification)
        func_obj: The actual function object (preferred if available)
    """
    try:
        key = get_function_key(func_obj, module_name, func_name)
        if key in overload_registry:
            del overload_registry[key]
    except ValueError:
        # If we can't get a key, just return
        pass

# Keep the original context manager, but simplify it
@contextmanager
def collect_overloads():
    """
    Context manager for collecting overloads during imports.

    Example:
        with collect_overloads():
            import my_module
            # Overloads from my_module will be collected
    """
    global is_active
    previous_state = is_active

    try:
        is_active = True
        skip_problematic_modules()  # Skip known problematic modules
        yield
    finally:
        is_active = previous_state
        scan_loaded_modules()  # Scan for implementations before exiting

def start_collection() -> Iterator[OverloadInfo]:
    """
    Enable overload collection and return a generator of collected overloads.

    Yields:
        OverloadInfo: Overload information for each function as it's processed

    Example:
        for info in start_collection():
            # Process each overload info
            write_to_db(info)
    """
    global is_active
    is_active = True
    skip_problematic_modules()  # Skip known problematic modules

    # Initial scan to process modules already loaded
    yield from scan_loaded_modules()

def stop_collection() -> Iterator[OverloadInfo]:
    """
    Disable overload collection and yield any remaining collected overloads.

    Yields:
        OverloadInfo: Any remaining overload information not yet processed
    """
    global is_active
    is_active = False

    # Process any remaining overloads
    for key, info in list(overload_registry.items()):
        yield info
        del overload_registry[key]

# Initialize by monkey-patching the overload decorator, but don't start collecting yet
initialize()
