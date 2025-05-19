FROM ubuntu:22.04

ARG HOUDINI_VERSION=20.0.547
ARG HOUDINI_BUILD=linux_arm64_gcc9.3

# Configure apt to cache and not install recommends
RUN echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/docker-clean \
    && echo 'APT::Install-Recommends "false";' >> /etc/apt/apt.conf.d/docker-clean

# Install certificates and update trust store before anything else
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates curl && \
    update-ca-certificates

# Install dependencies including python and pip
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    bc fontconfig wget curl python3 python3-pip \
    libasound2 libgl1 libglu1 libglu1-mesa libglx0 libice6 \
    libnss3 libopengl0 libpci3 libsm6 libx11-6 libx11-xcb1 libxcb-icccm4 \
    libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-render0 \
    libxss1 libxt6 libxtst6 \
    libxcb-shape0 libxcb-shm0 libxcb-sync1 libxcb-util1 libxcb-xfixes0 \
    libxcb-xinerama0 libxcb-xkb1 libxcb1 libxcomposite1 libxcursor1 libxdamage1 \
    libxext6 libxi6 libxkbcommon-x11-0 libxkbcommon0 libxrandr2 libxrender1 \
    gdb procps

# Create a downloads directory and cache the Houdini download
WORKDIR /tmp
RUN --mount=type=cache,target=/tmp/downloads \
    mkdir -p /tmp/downloads && \
    if [ ! -f /tmp/downloads/houdini-${HOUDINI_VERSION}.tar.gz ]; then \
        echo "Downloading Houdini ${HOUDINI_VERSION}..." && \
        curl -sSL -o /tmp/downloads/houdini-${HOUDINI_VERSION}.tar.gz \
        "https://www.sidefx.com/download/download-houdini-${HOUDINI_VERSION}/linux/houdini-${HOUDINI_VERSION}-${HOUDINI_BUILD}.tar.gz"; \
    fi && \
    cp /tmp/downloads/houdini-${HOUDINI_VERSION}.tar.gz /tmp/houdini.tar.gz

# Install Houdini
RUN tar -xzf /tmp/houdini.tar.gz && \
    cd houdini-* && \
    ./houdini.install --accept-EULA --no-license-server --make-dir /opt/hfs && \
    rm -rf /tmp/houdini*

# Install Python packages with caching
RUN --mount=type=cache,target=/root/.cache/pip \
    python3 -m pip install --upgrade pip && \
    python3 -m pip install debugpy

# Setup environment - NOTE: Fixed path from /top/hfs20.5 to /opt/hfs
ENV HFS=/opt/hfs
ENV PATH=$HFS/bin:$PATH
# Fixed double slash in path
ENV PYTHONPATH=/app/houdini/h20.5/src:$HFS/houdini/python3.11libs

RUN useradd -m -s /bin/bash houdini
USER houdini
WORKDIR /app
RUN mkdir -p /home/houdini/houdini

# Don't copy files in the Dockerfile - use volume mounts instead
# COPY . /app

ENTRYPOINT ["tail", "-f", "/dev/null"]
