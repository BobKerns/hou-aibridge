![Zabob and city banner](docs/images/zabob-banner.jpg)

# Command-line scripts

This is part of the root project of the [Zabob](../README.md) project.

It holds command-line scripts, for development and management.

The main tool for development is called [devtool](devtool).

It illustrates how to set up tools which can be run with a minimum of setup.

Python scripts intended to be run from the command-line should start with:

```python
#!/usr/bin/env uv run --script
```

This line should be followed by the following type of structured comment managed by `uv`:

```python
#!/usr/bin/env uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "click",
#     "requests",
#     "semver",
# ///
```

See [PEP 723](https://peps.python.org/pep-0723/) for more information.

The dependencies are added with:

```bash
uv add --script <script> dependency
```

or removed with:

```bash
uv remove --script <script> dependency
```

You should include _all_ the external dependencies your script needs to run, so that it does not require prior setup. `uv` will handle installation on a per-script basis using this information; it will not depend on the rest of the project being set up,

The remainder of the script ensues that the code can be run without setup, by adding to the `sys.path` all the internal paths needed.

The `# type: ignore` comments are needed because vscode does not know how to resolve these runtime references.

You can create your own pallet of commands like this:

```python
import click


from zabob.main import browse_docs

@click.group()
def cli():
    pass

cli.add_command(browse_docs, "readme")

if __name__ == '__main__':
    # Or skip the subcommands and call browse_docs() directly here.
    cli()
```

```python


from pathlib import Path
import sys
from typing import Final

# Make sure modules can be imported
SCRIPT: Final[Path] = Path(__file__).resolve()
SCRIPT_DIR: Final[Path] = SCRIPT.parent
PROJECT_DIR: Final[Path] = SCRIPT_DIR.parent
MODULES_DIR: Final[Path] = PROJECT_DIR / 'zabob-modules/src'
sys.path.insert(0, str(MODULES_DIR))

if __name__ == "__main__":
    from zabob import main  # type: ignore # noqa: E402
    main()

```
