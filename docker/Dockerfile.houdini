FROM ubuntu:22.04

ARG HOUDINI_VERSION=20.0.547
ARG HOUDINI_BUILD=linux_x86_64_gcc9.3

# Install dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    bc fontconfig wget libasound2 libgl1 libglu1 libglu1-mesa libglx0 libice6 \
    libnss3 libopengl0 libpci3 libsm6 libx11-6 libx11-xcb1 libxcb-icccm4 \
    libxcb-image0 libxcb-keysyms1libxcb-randr0 libxcb-render-util0 libxcb-render0 \
    libxcb-shape0 libxcb-shm0 libxcb-sync1 libxcb-util1 libxcb-xfixes0 \
    libxcb-xinerama0 libxcb-xkb1 libxcb1 libxcomposite1 libxcursor1 libxdamage1 \
    libxext6 libxi6 libxkbcommon-x11-0 libxkbcommon0 libxrandr2 libxrender1 \
    libxss1 libxt6 libxtst6 \
    && rm -rf /var/lib/apt/lists/*

# Download specific Houdini version
RUN wget -O houdini.tar.gz "https://www.sidefx.com/download/download-houdini-${HOUDINI_VERSION}/linux/houdini-${HOUDINI_VERSION}-${HOUDINI_BUILD}.tar.gz"

# Install Houdini
RUN tar -xzf houdini.tar.gz && \
    cd houdini-* && \
    ./houdini.install --accept-EULA --no-license-server --make-dir /opt/hfs

# Setup environment
ENV HFS=/opt/hfs
ENV PATH=$HFS/bin:$PATH

# Continue with your setup...
