# Zabob MCP Server

![Zabob and city banner](../docs/images/zabob-banner.jpg)

The Zabob Model Context Protocol (MCP) server provides AI assistants with powerful tools for working with SideFX Houdini.

## Quick Start with Docker 🐳

```bash
# Run the multi-architecture MCP server
docker run -d --name zabob-mcp -p 3000:3000 bobkerns/mcp-server:latest

# Check if it's running
curl http://localhost:3000/health
```

👉 **[Complete setup guide for Claude and other AI assistants](../docs/user/claude-docker-setup.md)**

## What's Included

- 🔍 Houdini node and parameter information
- 📚 Documentation and help system integration  
- 🛠️ MCP-compliant server architecture
- 🐳 Multi-platform Docker support (Intel x86_64 and ARM64)
- 🚀 Easy deployment and configuration

## For Developers

This is a subproject of the [zabob](../README.md) project. See the [development documentation](../docs/development/README.md) for information about:

- Building from source
- Contributing to the project
- API documentation
- Testing and debugging

## Architecture

The MCP server is built using:
- Python 3.13+ with FastMCP framework
- Async/await architecture for performance
- Docker multi-stage builds for minimal image size
- Support for both stdio and HTTP transports
