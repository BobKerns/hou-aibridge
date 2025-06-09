# Setting up Claude (and other AI assistants) with Zabob MCP Server via Docker

This guide shows you how to configure Claude Desktop and other MCP-compatible AI assistants to use the Zabob MCP server running in Docker.

## Prerequisites

- Docker installed on your system
- Claude Desktop app (or other MCP-compatible AI assistant)
- Internet connection to pull the Docker image

## Quick Start

### 1. Configure Claude Desktop

Add this configuration to your Claude Desktop MCP settings file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "zabob": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "bobkerns/mcp-server:latest"
      ],
      "env": {}
    }
  }
}
```

This configuration will:
- Pull the latest Zabob MCP server image (automatically selects the right architecture for your system)
- Run it interactively (`-i` flag for stdin/stdout communication)
- Automatically remove the container when done (`--rm` flag)
- No need to manage persistent containers or ports

### 2. Restart Claude Desktop

After updating the configuration file, restart Claude Desktop for the changes to take effect.

## Advanced Configuration

### Environment Variables

You can configure the MCP server using environment variables:

```json
{
  "mcpServers": {
    "zabob": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e", "LOG_LEVEL=debug",
        "bobkerns/mcp-server:latest"
      ],
      "env": {}
    }
  }
}
```

Available environment variables:

- `LOG_LEVEL`: Set logging level (debug, info, warning, error)

## Configuration for Other AI Assistants

### Cursor IDE

Add to your Cursor MCP configuration:

```json
{
  "mcp": {
    "servers": {
      "zabob": {
        "command": "docker",
        "args": ["run", "-i", "--rm", "bobkerns/mcp-server:latest"]
      }
    }
  }
}
```

### Continue.dev

Add to your `continue.json` configuration:

```json
{
  "mcpServers": [
    {
      "name": "zabob",
      "command": "docker",
      "args": ["run", "-i", "--rm", "bobkerns/mcp-server:latest"]
    }
  ]
}
```

## Troubleshooting

### Claude Desktop Not Recognizing the Server

1. **Check configuration file location**: Ensure you're editing the correct configuration file for your OS.

2. **JSON syntax**: Validate your JSON configuration using a JSON validator.

3. **Restart required**: Always restart Claude Desktop after configuration changes.

4. **Check logs**: Look for MCP-related errors in Claude Desktop's logs or console.

### Docker Issues

1. **Docker not running**: Ensure Docker Desktop is running on your system.

2. **Image not found**: If you get an error about the image not being found, try pulling it manually:

   ```bash
   docker pull bobkerns/mcp-server:latest
   ```

3. **Permission issues**: On Linux, you might need to add your user to the docker group or run with sudo.

## Multi-Architecture Support

The `bobkerns/mcp-server:latest` image supports both Intel (x86_64) and ARM64 architectures, so it will work on:

- Intel/AMD computers (Windows, Linux, macOS)
- Apple Silicon Macs (M1, M2, M3)
- ARM64 Linux servers

Docker automatically pulls the correct architecture for your system.

## Next Steps

Once you have the MCP server running and connected to Claude:

1. Try asking Claude about Houdini-related questions to test the connection
2. Explore the available MCP tools and resources
3. Check out the [MCP Server Documentation](../mcp-server/README.md) for more advanced usage

## Getting Help

If you encounter issues:

1. Check the [troubleshooting section](#troubleshooting) above
2. Review the container logs for error messages
3. Open an issue on the [Zabob GitHub repository](https://github.com/yourusername/zabob/issues)
