# Dockerfile for MCP Git server with Git LFS support
# Extends the official mcp/git image to add git-lfs

FROM mcp/git:latest

# Install git-lfs
RUN apt-get update && \
    apt-get install -y git-lfs && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /var/cache/apk/*

# Verify installation
RUN git lfs version

# The base image already sets up the MCP server
# We just need to make sure git-lfs is available
