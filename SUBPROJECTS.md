![Zabob and city banner](docs/images/zabob-banner.jpg)

# Project hierarchy

This project is organized into subprojects. You are currently examining this via the [main project](/README.md). The main project should always be the first.

Rather than opening this directory directly, you should open the workspace, [zabob.code-workspace](zabob.code-workspace) via the `File` / `Open Workspace from File...` command. This will ensure you get the correctly-scoped settings. The workspace settings are managed in the `.code-workspace` file, but the individual subprojects (including the main project) can have their own settings.

The subprojects:

| Subproject | Description |
|------------|-------------|
| [zabob](README.md) | This is actually the root directory of the project. |
| [mcp-server](mcp-server/README.md) | Main control and processing server |
| [h20.5](houdini/h20.5) | Connector for Houdini 20.5 |
| [h21.0](houdini/h21.0/README.md) | Connector for Houdini 21.0 when released |
| [hdas](hdas/README.md)| Future home of HDA for Houdini-side connection. |
| [zabob-modules](zabob-modules/README.md) | Shared modules and libraries for Zabob |
| [zabob-chat](zabob-chat/README.md) | Chat interface and related services |
| [docker](docker/README.md) | Docker configurations and deployment files |
| [docs](docs/README.md) | Project documentation and guides |

## Setup

* To find the right dictionary, each subproject needs a `.vscode/settings.json` file. It can be a empty JSON object unless per-subproject settings are needed.

```jsonc
{
}
```

The spelling dictionary is stored in [docs/.cspell/workspace.txt], rather than the top-level project, because there is no way to reference the top-level project that doesn't change if the directory name of the worktree changes. All projects share the same dictionary, and currently all the same settings, stored in the [zabob.code-workspace](zabob.code-workspace) file.

The settings appear in the UI like this. User settings are personal, unshared changes. Workspace settings apply to the entire workspace (and are stored in [zabob.code-workspace](zabob.code-workspace), as described above). The "Folder" settings drop-down selects the per-project settings.

## Referencing subprojects in `pyproject.py` files

Here's an explanation of [when to use dot notation, hyphens, or underscores](PYPROJECT-TOML.md)
