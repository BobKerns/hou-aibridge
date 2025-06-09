![Zabob and city banner](docs/images/zabob-banner.jpg)

# Understanding Package Naming Across Different TOML Sections

`pyproject.toml` can be very confusing. One particularly confusing point is when to use dot notation, when to use hyphens, and when to use underscores. Here's Claude 3.7 Sonnet's explanation:

## PyPI Package Names (use hyphens)

Used in these sections:

```toml
[project]
name = "zabob-h20-5"  # PyPI package name uses hyphens

[tool.uv.sources]
zabob-h20-5 = { workspace = true }  # Must match project.name
```

## Python Import Paths (use dots and underscores)

Used in these sections:

```toml
[tool.setuptools]
packages = ["zabob.h20_5"]  # How Python imports it

[project.scripts]
h20-5 = "zabob.h20_5:main"  # Right side is Python import path
```

## Command-Line Names (can use hyphens)

Used in script definition keys:

```toml
[project.scripts]
h20-5 = "zabob.h20_5:main"  # Left side is the command name
```

## The Mapping Logic

1. PyPI package `zabob-h20-5` → Python import `zabob.h20_5`
2. Directory structure matches Python import: h20_5
3. Command `h20-5` executes the function `main()` in module `zabob.h20_5`

This is why it's confusing - you're constantly translating between these different naming conventions within the same file!

## Common Pitfalls

- **Missing `__init__.py`**: For namespace packages, don't add an `__init__.py` in the top-level directory (`zabob/`), but do add it in subdirectories (`zabob/h20_5/`)

- **Directory structure mismatch**: Ensure your directories match the package names: `src/zabob/h20_5/` not `src/zabob-h20_5/`

- **Inconsistent naming**: If your project is named `zabob-h20-5`, your uv source should also be `zabob-h20-5`

## Example Directory Structure

```text
houdini/h20.5/
├── pyproject.toml
└── src/
    └── zabob/         # No __init__.py here (namespace package)
        └── h20_5/     # Contains __init__.py
            ├── __init__.py
            └── other_modules.py
```

## Build Backend Differences

- **setuptools**: Uses `packages = ["zabob.h20_5"]`
- **hatchling**: Often relies on automatic discovery with `include = ["src/*"]`
