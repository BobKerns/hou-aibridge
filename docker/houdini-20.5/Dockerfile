# Stage 1: Common base layer
FROM ubuntu:22.04 AS base

# Configure apt
RUN echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/docker-clean \
    && echo 'APT::Install-Recommends "false";' >> /etc/apt/apt.conf.d/docker-clean

# Install core dependencies including Python and UV
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates curl python3 python3-pip && \
    update-ca-certificates && \
    pip3 install uv

# Stage 2: Builder - Downloads Houdini installer
FROM base AS downloader

ARG HOUDINI_VERSION=20.5.584
ARG HOUDINI_ARCH=arm64
ARG HOUDINI_BUILD_TYPE=gcc9.3

# Copy the script
COPY houdini_versions /tmp/houdini_versions

# Use secret mount for credentials with the new --credentials option
RUN --mount=type=secret,id=sidefx_credentials \
    chmod +x /tmp/houdini_versions && \
    mkdir -p /tmp/downloads && \
    cd /tmp && \
    uv run /tmp/houdini_versions download \
        --version $HOUDINI_VERSION \
        --arch $HOUDINI_ARCH \
        --build-type $HOUDINI_BUILD_TYPE \
        --credentials /run/secrets/sidefx_credentials \
        --output-path /tmp/houdini.tar.gz

# Stage 3: Final image with Houdini
FROM base AS final

# Install Houdini-specific dependencies
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    bc fontconfig wget \
    libasound2 libgl1 libglu1 libglu1-mesa libglx0 libice6 \
    libnss3 libopengl0 libpci3 libsm6 libx11-6 libx11-xcb1 libxcb-icccm4 \
    libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-render0 \
    libxss1 libxt6 libxtst6 \
    libxcb-shape0 libxcb-shm0 libxcb-sync1 libxcb-util1 libxcb-xfixes0 \
    libxcb-xinerama0 libxcb-xkb1 libxcb1 libxcomposite1 libxcursor1 libxdamage1 \
    libxext6 libxi6 libxkbcommon-x11-0 libxkbcommon0 libxrandr2 libxrender1 \
    gdb procps

# Copy the Houdini installer from the downloader stage
COPY --from=downloader /tmp/houdini.tar.gz /tmp/houdini.tar.gz

# Install Houdini
RUN tar -xzf /tmp/houdini.tar.gz && \
    cd houdini-* && \
    ./houdini.install --accept-EULA --no-license-server --make-dir /opt/hfs && \
    rm -rf /tmp/houdini*

# Install Python packages with caching
RUN --mount=type=cache,target=/root/.cache/pip \
    uv pip install --system debugpy

# Set up environment
ENV HFS=/opt/hfs
ENV PATH=$HFS/bin:$PATH
ENV PYTHONPATH=/app/houdini/h20.5/src:$HFS/houdini/python3.11libs

RUN useradd -m -s /bin/bash houdini
USER houdini
WORKDIR /app

ENTRYPOINT ["tail", "-f", "/dev/null"]
