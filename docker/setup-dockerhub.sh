#!/bin/bash
# Docker Hub Setup Script for Zabob MCP Server

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}     Zabob MCP Server - Docker Hub Setup      ${NC}"
echo -e "${BLUE}================================================${NC}"
echo

# Check if Docker is running
if ! docker version >/dev/null 2>&1; then
    error "Docker is not running or not accessible"
    echo "Please start Docker Desktop and try again"
    exit 1
fi

log "Docker is running and accessible"

# Check current Docker login status
if docker info 2>/dev/null | grep -q "Username:"; then
    CURRENT_USER=$(docker info 2>/dev/null | grep "Username:" | awk '{print $2}')
    log "Already logged in to Docker Hub as: $CURRENT_USER"

    read -p "Do you want to use this username? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        export DOCKER_USERNAME="$CURRENT_USER"
        log "Using existing Docker Hub username: $DOCKER_USERNAME"
    else
        info "You can logout with: docker logout"
        info "Then run this script again to login with a different account"
        exit 0
    fi
else
    warn "Not currently logged in to Docker Hub"

    # Prompt for username
    read -p "Enter your Docker Hub username: " DOCKER_USERNAME

    if [ -z "$DOCKER_USERNAME" ]; then
        error "Username cannot be empty"
        exit 1
    fi

    log "Logging in to Docker Hub as: $DOCKER_USERNAME"

    # Login to Docker Hub
    if docker login --username "$DOCKER_USERNAME"; then
        log "Successfully logged in to Docker Hub"
        export DOCKER_USERNAME
    else
        error "Failed to login to Docker Hub"
        exit 1
    fi
fi

# Verify buildx is available
if ! docker buildx version >/dev/null 2>&1; then
    error "Docker buildx is not available"
    echo "Please install Docker Desktop or enable buildx plugin"
    exit 1
fi

log "Docker buildx is available"

# Create buildx builder if needed
BUILDER_NAME="zabob-multiarch"
if ! docker buildx inspect "$BUILDER_NAME" >/dev/null 2>&1; then
    log "Creating multi-platform builder: $BUILDER_NAME"
    docker buildx create --name "$BUILDER_NAME" --driver docker-container --use
    docker buildx inspect --bootstrap
else
    log "Multi-platform builder already exists: $BUILDER_NAME"
    docker buildx use "$BUILDER_NAME"
fi

echo
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}               Setup Complete!                 ${NC}"
echo -e "${GREEN}================================================${NC}"
echo
log "Docker Hub username: $DOCKER_USERNAME"
log "Multi-platform builder: $BUILDER_NAME"
echo
info "You can now run the build script:"
echo -e "${BLUE}  export DOCKER_USERNAME=$DOCKER_USERNAME${NC}"
echo -e "${BLUE}  ./docker/build-multiarch.sh${NC}"
echo
info "Or build with a specific version tag:"
echo -e "${BLUE}  ./docker/build-multiarch.sh v1.0.0${NC}"
echo
