import sys
import os
from pathlib import Path
import runpy
import code# Add after setting sys.prefix in sitecustomize.py
import sysconfig

# Store original functions
_original_get_path = sysconfig.get_path
_original_get_paths = sysconfig.get_paths

# This will be templated during installation
VENV_PATH = Path(__file__).resolve().parent.parent

# Always set up the virtual environment properly
# Store original base_prefix if not already set
if not hasattr(sys, 'base_prefix'):
    sys.base_prefix = sys.prefix

# Set prefix to venv path - this is critical for venv detection
sys.prefix = str(VENV_PATH)

# Process Python flags appropriately
flags_processed = []
skip_next = False
flag_handlers = {
    '-B': lambda: os.environ.setdefault('PYTHONDONTWRITEBYTECODE', 'x'),
    '-v': lambda: os.environ.setdefault('PYTHONVERBOSE', '1'),
    '-I': lambda: None,  # Ignore isolated mode, we need site-packages
    '-S': lambda: None,  # Ignore "no site" flag, we need site
    '-E': lambda: None,  # Ignore "ignore environment" flag
}

# Detect if we're being run as the main script
is_main_script = len(sys.argv) > 0 and sys.argv[0].endswith('sitecustomize.py')

# Process arguments if we're the main script
if is_main_script:
    i = 1  # Skip sitecustomize.py
    while i < len(sys.argv):
        arg = sys.argv[i]

        # Check if this is a flag
        if arg.startswith('-'):
            if arg in flag_handlers:
                flag_handlers[arg]()
                flags_processed.append(i)
            elif arg in ('-c', '-m'):
                # These flags indicate end of Python options
                break

        i += 1

    # Remove processed flags from argv
    for i in sorted(flags_processed, reverse=True):
        sys.argv.pop(i)


def patched_get_path(name, scheme:str|None=None, vars=None, expand=True):
    if vars is None:
        vars = {}

    # Set default scheme based on platform if None provided
    if scheme is None:
        if os.name == 'nt':
            scheme = 'nt'
        else:
            scheme = 'posix_prefix'
            
    # Always ensure these point to our venv
    vars['base'] = str(VENV_PATH)
    vars['platbase'] = str(VENV_PATH)

    # Special handling for purelib and platlib paths
    if name in ('purelib', 'platlib') and scheme in (None, 'posix_prefix', 'nt'):
        pyver = f"python{sys.version_info.major}.{sys.version_info.minor}"
        return str(VENV_PATH / "lib" / pyver / "site-packages")

    return _original_get_path(name, scheme, vars, expand)

def patched_get_paths(scheme: str, vars=None, expand=True):
    if vars is None:
        vars = {}

    # Always ensure these point to our venv
    vars['base'] = str(VENV_PATH)
    vars['platbase'] = str(VENV_PATH)

    paths = _original_get_paths(scheme, vars, expand)

    # Always ensure site-packages points to our venv
    pyver = f"python{sys.version_info.major}.{sys.version_info.minor}"
    site_packages = str(VENV_PATH / "lib" / pyver / "site-packages")
    paths['purelib'] = site_packages
    paths['platlib'] = site_packages

    return paths

# Apply the patches
sysconfig.get_path = patched_get_path
sysconfig.get_paths = patched_get_paths

# Always ensure site-packages is in path, even with -I flag
pyver = f"python{sys.version_info.major}.{sys.version_info.minor}"
site_packages = Path(VENV_PATH) / "lib" / pyver / "site-packages"
site_packages.mkdir(parents=True, exist_ok=True)
if str(site_packages) not in sys.path:
    sys.path.insert(1, str(site_packages))


lib_dir = VENV_PATH / "lib"
os.environ["PYTHONPLATLIBDIR"] = str(lib_dir)

# Print diagnostic info when in debug mode
if os.environ.get("ZABOB_DEBUG") == "1":
    print(f"sitecustomize.py: sys.prefix = {sys.prefix}", file=sys.stderr)
    print(f"sitecustomize.py: sys.base_prefix = {sys.base_prefix}", file=sys.stderr)
    print(f"sitecustomize.py: sys.path = {sys.path}", file=sys.stderr)

# Only take over execution if we're being run directly
if len(sys.argv) > 0 and sys.argv[0].endswith('sitecustomize.py'):
    # Remove sitecustomize.py from argv
    sys.argv.pop(0)

    # Handle different execution modes
    if not sys.argv:
        # No arguments - check if we're in interactive mode
        is_interactive = sys.stdin.isatty()

        if is_interactive:
            # Interactive terminal mode
            sys.ps1 = "hython>>> "  # Custom prompt for hython
            sys.ps2 = "hython... "
            print(f"Houdini Python {sys.version} in virtual environment {VENV_PATH}")
            console = code.InteractiveConsole()
            console.interact(banner="")
        else:
            # Non-interactive mode (piped input)
            # Use InteractiveConsole but suppress prompts
            console = code.InteractiveConsole()

            # Monkey patch to suppress prompts in non-interactive mode
            console.write = lambda data: None

            # Feed input line by line exactly as the normal REPL would
            while True:
                try:
                    line = sys.stdin.readline()
                    if not line:  # EOF
                        break
                    console.push(line)
                except KeyboardInterrupt:
                    break

        # Exit after interactive session or script execution
        sys.exit(0)
    else:
        # We have arguments - handle different modes
        arg = sys.argv.pop(0)

        try:
            if arg == '-m':
                # Module mode (-m)
                if not sys.argv:
                    print("Error: No module specified", file=sys.stderr)
                    sys.exit(1)

                module_name = sys.argv[0]  # Keep module name in argv
                sys.argv[0] = "__main__"  # Set argv[0] to __main__ as Python does
                runpy.run_module(module_name, run_name="__main__", alter_sys=True)

            elif arg == '-c':
                # Command mode (-c)
                if not sys.argv:
                    print("Error: No command specified", file=sys.stderr)
                    sys.exit(1)

                cmd = sys.argv.pop(0)
                sys.argv.insert(0, "-c")  # Python sets argv[0] to -c
                exec(cmd)

            else:
                # Script mode (normal execution)
                script_path = arg
                sys.path.insert(0, str(Path(script_path).parent.resolve()))
                with open(script_path) as f:
                    script_content = f.read()

                # Set argv[0] to the script name
                sys.argv.insert(0, script_path)

                # Run the script
                globals_dict = {
                    "__name__": "__main__",
                    "__file__": script_path,
                    "__builtins__": __builtins__,
                }
                exec(compile(script_content, script_path, 'exec'), globals_dict)

        except Exception:
            import traceback
            traceback.print_exc()
            sys.exit(1)

        # Exit after executing
        sys.exit(0)
