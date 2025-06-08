#!/bin/bash
# Build script for MCP Git server with Git LFS support

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🔨 Building MCP Git server with Git LFS support..."

# Build the Docker image
docker build -t mcp/git-lfs:latest .

echo "✅ Build complete!"
echo "📝 To use this image, update your Claude MCP config:"
echo "   Change 'mcp/git' to 'mcp/git-lfs' in the docker args"
