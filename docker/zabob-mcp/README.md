# Zabob MCP Server Docker Container

This directory contains the Docker configuration for the Zabob MCP (Model Context Protocol) Server, which provides AI agents with access to comprehensive Houdini Python API information.

## Files

- `Dockerfile` - Multi-stage Docker build configuration
- `docker-compose.yml` - Docker Compose configuration for easy deployment
- `README.md` - This file

## Building the Docker Image

```bash
cd /Users/rwk/p/zabob/docker/zabob-mcp
docker build -t docker-zabob-mcp:latest .
```

## Running the Container

### Using Docker directly

```bash
# Run with help information
docker run --rm docker-zabob-mcp:latest --help

# Run the MCP server (interactive mode)
docker run --rm -it docker-zabob-mcp:latest

# Run in background
docker run -d --name zabob-mcp docker-zabob-mcp:latest
```

### Using Docker Compose

```bash
# Start the service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the service
docker-compose down
```

## Container Details

- **Base Image**: Python 3.13-slim
- **Package Manager**: uv (for fast dependency installation)
- **Database**: Includes Houdini API database at `/app/dev_out/20.5.584/houdini_data_dev.db`
- **Working Directory**: `/app`

## Available MCP Tools

The server provides the following MCP tools:
- `get_functions_returning_nodes` - Find functions that return Houdini node objects
- `search_functions` - Search functions by keyword in name or docstring
- `get_primitive_functions` - Find functions related to primitive operations
- `get_modules_summary` - Get summary of all Houdini modules with function counts
- `search_node_types` - Search node types by keyword
- `get_node_types_by_category` - Get node types filtered by category (Sop, Object, Dop, etc.)
- `get_database_stats` - Get statistics about the Houdini database contents
- `query_response` - Handle general queries (legacy tool)

## Multi-stage Build

The Dockerfile uses a multi-stage build approach:
1. **Dependencies stage**: Installs Python dependencies using uv
2. **Runtime stage**: Copies the application and dependencies for a smaller final image

## Troubleshooting

If you encounter issues:

1. **Build errors**: Ensure all dependencies are properly specified in the pyproject.toml files
2. **Runtime errors**: Check that the database file exists and is accessible
3. **Import errors**: Verify that all required Python packages are installed

## Development

To modify the container for development:

1. Edit the source code in the zabob project directories
2. Rebuild the Docker image: `docker build -t docker-zabob-mcp:latest .`
3. Test the changes: `docker run --rm docker-zabob-mcp:latest --help`
