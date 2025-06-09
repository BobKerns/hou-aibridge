#!/bin/bash
# Build Python wheels for multiple architectures

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

DIST_DIR="dist"
VERSION="${1:-$(date +%Y%m%d%H%M%S)}"

# Clean previous builds
log "Cleaning previous builds..."
rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR"

# Python packages to build
PACKAGES=(
    "zabob-modules"
    "houdini/zcommon"
    "mcp-server"
    "houdini/h20.5"
)

# Build for current architecture first
log "Building wheels for current architecture..."
for package in "${PACKAGES[@]}"; do
    if [ -f "$package/pyproject.toml" ]; then
        log "Building $package..."
        cd "$package"

        # Build wheel
        uv build --wheel --out-dir "../$DIST_DIR"

        # Build sdist (source distribution - architecture independent)
        uv build --sdist --out-dir "../$DIST_DIR"

        cd - > /dev/null
    else
        warn "No pyproject.toml found in $package, skipping..."
    fi
done

# If running on Apple Silicon, also build universal wheels
if [[ "$(uname -m)" == "arm64" && "$(uname -s)" == "Darwin" ]]; then
    log "Building universal wheels for macOS..."

    # Install cibuildwheel for cross-platform builds
    if ! command -v cibuildwheel &> /dev/null; then
        log "Installing cibuildwheel..."
        uv tool install cibuildwheel
    fi

    for package in "${PACKAGES[@]}"; do
        if [ -f "$package/pyproject.toml" ]; then
            log "Building universal wheel for $package..."
            cd "$package"

            # Build universal wheels for macOS
            CIBW_ARCHS_MACOS="x86_64 arm64 universal2" \
            CIBW_BUILD="cp311-* cp312-* cp313-*" \
            cibuildwheel --output-dir "../$DIST_DIR"

            cd - > /dev/null
        fi
    done
fi

log "Build completed! Wheels available in $DIST_DIR/"
ls -la "$DIST_DIR/"
