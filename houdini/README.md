# Houdini connector subprojects

This folder groups the houdini-version-specific connector subprojects.

The VS Code workspace configuration suppresses the contents of the individual projects in the explorer view of this directory.

Instead, they should be visible in the top level as subprojects:
![Explorer sidebar](docs/images/houdini/explorer-houdini.png)

This is managed in the[workspace settings](../zabob.code-workspace) via the `files.exclude` setting:

```json
            "houdini/h*.*/": true,
```

The [houdini/common](zcommon/README.md)
