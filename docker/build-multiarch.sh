#!/bin/bash
# Multi-architecture Docker build script for Zabob

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

# Check if buildx is available
if ! docker buildx version >/dev/null 2>&1; then
    error "Docker buildx is not available. Please install Docker Desktop or enable buildx."
    exit 1
fi

# Create a new builder instance for multi-platform builds
BUILDER_NAME="zabob-multiarch"

log "Setting up multi-platform builder..."
if ! docker buildx inspect "$BUILDER_NAME" >/dev/null 2>&1; then
    log "Creating new buildx builder: $BUILDER_NAME"
    docker buildx create --name "$BUILDER_NAME" --driver docker-container --use
else
    log "Using existing builder: $BUILDER_NAME"
    docker buildx use "$BUILDER_NAME"
fi

# Bootstrap the builder
log "Bootstrapping builder..."
docker buildx inspect --bootstrap

# Build multi-platform images
PLATFORMS="linux/amd64,linux/arm64"

# Docker Hub requires format: username/repository-name
# Try multiple methods to get Docker Hub username
DOCKER_USERNAME="${DOCKER_USERNAME:-}"

if [ -z "$DOCKER_USERNAME" ]; then
    # Try to get username from docker config
    if [ -f ~/.docker/config.json ]; then
        DOCKER_USERNAME=$(jq -r '.auths["https://index.docker.io/v1/"].username // empty' ~/.docker/config.json 2>/dev/null)
    fi
fi

if [ -z "$DOCKER_USERNAME" ]; then
    # Try to get from docker credential helper
    DOCKER_USERNAME=$(docker-credential-desktop list 2>/dev/null | jq -r '.["https://index.docker.io/v1/"]' 2>/dev/null || echo "")
fi

if [ -z "$DOCKER_USERNAME" ]; then
    error "Docker Hub username not found. Please:"
    echo "1. Set DOCKER_USERNAME environment variable:"
    echo "   export DOCKER_USERNAME=your-dockerhub-username"
    echo "2. Or login to Docker Hub:"
    echo "   docker login"
    echo "3. Then run this script again"
    exit 1
fi

log "Using Docker Hub username: $DOCKER_USERNAME"
TAG_PREFIX="$DOCKER_USERNAME"
VERSION="${1:-latest}"

log "Building Zabob MCP Server for platforms: $PLATFORMS"
docker buildx build \
    --platform "$PLATFORMS" \
    --file docker/zabob-mcp/Dockerfile \
    --tag "${TAG_PREFIX}/mcp-server:${VERSION}" \
    --tag "${TAG_PREFIX}/mcp-server:latest" \
    --push \
    .

log "Multi-platform build completed successfully!"
log "Images available for: $PLATFORMS"
log "Tags created:"
log "  - ${TAG_PREFIX}/mcp-server:${VERSION}"
log "  - ${TAG_PREFIX}/mcp-server:latest"

log "Note: Houdini development container build skipped for demo purposes."
log "The MCP server contains the Houdini database and is sufficient for most use cases."
