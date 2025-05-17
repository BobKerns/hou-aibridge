![Zabob and city banner](docs/images/zabob-banner.jpg)

# Project hierarchy

This project is organized into subprojects. You are currently examining this via the [main project](/README.md). The main project should always be the first.

Rather than opening this directory directly, you should open the workspace, [ai-bridge.code-workspace](hou-ai-bridge.code-workspace) via the `File` / `Open Workspace from File...` command. This will ensure you get the correctly-scoped settings. The workspace settings are managed in the `.code-workspace` file, but the individual subprojects (including the main project) can have their own settings.

The subprojects:

* [vscode-chat](vscode-chat/README.md)
* [mcp-server](mcp-server/README.md)
* [h20.5](houdini/h20.5) -- Connector for Houdini 20.5
* [h21.0](houdini/h21.0/README.md)  -- Connector for Houdini 21.0 when released
* [docker](docker/README.md)
* [docs](docs/README.md)
* [scripts](scripts/README.md)

## Setup

* To find the right dictionary, each subproject needs a `.vscode/settings.json` file. It can be a empty JSON object unless per-subproject settings are needed.

```jsonc
{
}
```

The spelling dictionary is stored in [docs/.cspell/workspace.txt], rather than the top-level project, because there is no way to reference the top-level project that doesn't change if the directory name of the worktree changes. All projects share the same dictionary, and currently all the same settings, stored in the [ai-bridge.code-workspace](ai-bridge.code-workspace) file.

The settings appear in the UI like this. User settings are personal, unshared changes. Workspace settings apply to the entire workspace (and are stored in [ai-bridge.code-workspace](ai-bridge.code-workspace), as described above). The "Folder" settings drop-down selects the per-project settings.
