# Zabob: The AI Bri## Features

* 🔗 Connects Claude, Copilot, and other MCP-aware chat interfaces to Houdini knowledge
* 🐳 Multi-architecture Docker support (Intel x86_64 and ARM64)
* 🎯 Easy setup with pre-built Docker images
* 📚 Access to Houdini documentation and node information
* 🛠️ Extensible MCP server architectureHoudini SFX

![Zabob in front of a future city](docs/images/zabob-holodeck-text.jpg)

This is a bridge from Copilot in VS Code, or any MCP-capable client, to knowledge about Houdini and Houdini networks.

## Quick Start 🚀

Want to use Zabob with Claude or another AI assistant right now?

👉 **[Follow our Docker setup guide](docs/user/claude-docker-setup.md)**

Just add this to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "zabob": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "bobkerns/mcp-server:latest"]
    }
  }
}
```

Then configure your AI assistant to connect to the MCP server. Full instructions in the [user documentation](docs/user/README.md).

## Features

* 🔗 Connects Claude, Copilot, and other MCP-aware chat interfaces to Houdini knowledge
* 🐳 Multi-architecture Docker support (Intel x86_64 and ARM64)  
* 🎯 Easy setup with pre-built Docker images
* 📚 Access to Houdini documentation and node information
* 🛠️ Extensible MCP server architecture

## Requirements

If you have any requirements or dependencies, add a section describing those and how to install and configure them.

## Extension Settings

TODO:
Include if your extension adds any VS Code settings through the `contributes.configuration` extension point.

For example:

This extension contributes the following settings:

\[TBD]

* `myExtension.enable`: Enable/disable this extension.
* `myExtension.thing`: Set to `blah` to do something.

## Known Issues

Need to return real data...

## Release Notes

See [CHANGELOG.md](CHANGELOG.md) for release notes

---

## Following extension guidelines

Ensure that you've read through the extensions guidelines and follow the best practices for creating your extension.

* [Extension Guidelines](https://code.visualstudio.com/api/references/extension-guidelines)

## Working with Markdown

You can author your README using Visual Studio Code. Here are some useful editor keyboard shortcuts:

* Split the editor (`Cmd+\` on macOS or `Ctrl+\` on Windows and Linux).
* Toggle preview (`Shift+Cmd+V` on macOS or `Shift+Ctrl+V` on Windows and Linux).
* Press `Ctrl+Space` (Windows, Linux, macOS) to see a list of Markdown snippets.

## For more information

* [Visual Studio Code's Markdown Support](http://code.visualstudio.com/docs/languages/markdown)
* [Markdown Syntax Reference](https://help.github.com/articles/markdown-basics/)

**Enjoy!**

## Development

This is still in early-stage development, but you can read the [development plan](DEVELOPMENT.md) and details about how the development environment works.

Contributions are encouraged! You can read the [contribution policy](CONTRIBUTING.md) and the [Code of Conduct](CODE_OF_CONDUCT.md)

## Subprojects

This project is divided into [subprojects](SUBPROJECTS.md). As a result, the VSCode explorer view does not exactly match the structure of the file system. For example, the [houdini/](houdini/README.md) folder holds multiple Houdini connection projects; these are presented in the explorer as being at top level, siblings to the root of the project.

In addition, I have enabled collapsing multiple related files into a single collapsed entry. The top-level `README.md` can be expanded to reveal the various top-level `.md` files, and `packages.json` displays the `.lock` file as a child. This helps minimize clutter in the explorer view.

## Release Process

This will have the [Release process](RELEASE.md) when it's ready.

## Security Policy

Here is the [Security policy](SECURITY.md).

## License

[MIT License](LICENSE.md)
