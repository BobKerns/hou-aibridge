![Zabob and city banner](docs/images/zabob-banner.jpg)

# Project scripts

This folder holds project-wide scripts. This is the directory to edit the scripts. The `.venv/` is set up for the scripts, the entries in `bin/` are symlinks.

This is not the folder to put on your `$PATH`. Put the `bin/` folder on your path instead, and if the script is intended to be run from the command-line, symlink it from `bin/` to here.

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
