![Zabob and city banner](docs/images/zabob-banner.jpg)

# Project hierarchy

This project is organized into subprojects. You are currently examining this via the [main project](/README.md). The main project should always be the first.

Rather than opening this directory directly, you should open the workspace, [hou-ai-bridge.code-workspace](hou-ai-bridge.code-workspace) via the `File` / `Open Workspace from File...` command. This will ensure you get the correctly-scoped settings. The workspace settings are managed in the `.code-workspace` file, but the individual subprojects (including the main project) can have their own settings.

The subprojects:

* [vscode-chat](vscode-chat/README.md)
* [mcp-server](mcp-server/README.md)
* [h20.5](houdini/h20.5) -- Connector for Houdini 20.5
* [h21.0](houdini/h21.0/README.md)  -- Connector for Houdini 21.0 when released
* [scripts](scripts/README.md)

## Setup

* To find the right dictionary, each subproject needs a `.vscode/settings.json` with a `cSpell.customDictionaries` entry, like this:

```jsonc
{
    // ...
    "cSpell.customDictionaries": {
        "workspace dictionary": {
            "path": "${workspaceFolder}/../.cspell/workspace.txt",
            "addWords": true,
            "name": "Project",
            "description": "Workspace dictionary for hou-ai-bridge",
            "scope": "workspace",
        }

    },
    // ...
}
```

For the Houdini-version subprojects, `../` becomes `../../`. We can't use `${workspacefolder:<main name>}`, because that name varies by the name of the worktree directory.
