# User Documentation

Welcome to the Zabob project user documentation! This section contains guides for end users who want to use Zabob with their AI assistants.

## Getting Started

### Quick Setup Guides

- **[Setting up Claude with Docker](claude-docker-setup.md)** - Complete guide for configuring Claude Desktop to use the Zabob MCP server via Docker
- **[Using Zabob with Houdini](houdini-integration.md)** - How to integrate Zabob into your Houdini workflow *(coming soon)*

### What is Zabob?

Zabob is a Model Context Protocol (MCP) server that provides AI assistants like Claude with powerful tools for working with SideFX Houdini. It allows you to:

- Query Houdini documentation and help
- Get information about nodes, parameters, and workflows
- Access Houdini-specific knowledge through natural language

### Supported AI Assistants

Zabob works with any MCP-compatible AI assistant, including:

- **Claude Desktop** (Anthropic)
- **Cursor IDE** 
- **Continue.dev**
- Any other MCP-compatible application

## Choose Your Setup Method

### 🐳 Docker (Recommended)

The easiest way to get started is using our pre-built Docker images:

👉 **[Follow the Docker setup guide](claude-docker-setup.md)**

**Pros:**
- No installation required
- Works on all platforms (Intel, ARM64, macOS, Windows, Linux)
- Automatic updates
- Isolated environment

### 🔧 Local Development Setup

For developers or advanced users who want to modify Zabob:

👉 **[See development documentation](../development/README.md)**

**Pros:**
- Full control over the codebase
- Can make custom modifications
- Access to development tools

## Need Help?

- Check the [troubleshooting section](claude-docker-setup.md#troubleshooting) in the Docker setup guide
- Review the [development documentation](../development/README.md)
- Open an issue on our [GitHub repository](https://github.com/yourusername/zabob/issues)

## What's Next?

Once you have Zabob running with your AI assistant:

1. Try asking questions about Houdini nodes and workflows
2. Explore the available MCP tools and capabilities
3. Check out example prompts and use cases *(coming soon)*