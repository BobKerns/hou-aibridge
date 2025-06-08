# Multi-stage Docker build for Zabob MCP Server
FROM python:3.13-slim AS base

# Install UV for fast Python package management
RUN pip install uv

# Create app directory
WORKDIR /app

# Stage 2: Dependencies
FROM base AS deps

# Copy dependency files and all source code needed for editable installs
COPY mcp-server/pyproject.toml ./mcp-server/
COPY zabob-modules/pyproject.toml ./zabob-modules/
COPY houdini/zcommon/pyproject.toml ./houdini/zcommon/

# Copy all source directories needed for dependencies
COPY mcp-server/src ./mcp-server/src
COPY zabob-modules/src ./zabob-modules/src
COPY houdini/zcommon/src ./houdini/zcommon/src
COPY houdini/zcommon/README.md ./houdini/zcommon/

# Install dependencies using UV
RUN cd mcp-server && uv pip install --system -e .

# Stage 3: Final runtime image
FROM base AS final

# Copy dependencies from deps stage
COPY --from=deps /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# Create app structure
WORKDIR /app

# Copy all source code
COPY mcp-server/src ./mcp-server/src
COPY zabob-modules/src ./zabob-modules/src
COPY houdini/zcommon/src ./houdini/zcommon/src

# Create a dummy .venv directory to satisfy the server's path check
RUN mkdir -p ./mcp-server/.venv

# Copy the database
COPY dev_out ./dev_out

# Set Python path to include all source directories
ENV PYTHONPATH=/app/mcp-server/src:/app/zabob-modules/src:/app/houdini/zcommon/src

# Expose port (not strictly necessary for MCP but useful for debugging)
EXPOSE 8000

# Set the working directory to match the script's expectations
WORKDIR /app

# Use the script directly as entrypoint
ENTRYPOINT ["python", "/app/mcp-server/src/zabob/mcp/server.py"]
