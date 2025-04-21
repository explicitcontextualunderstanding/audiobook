#!/bin/bash
set -e

# Install essential system dependencies
apt-get update && apt-get install -y --no-install-recommends \
    wget curl git ca-certificates software-properties-common && \
    rm -rf /var/lib/apt/lists/*

# Install ffmpeg
/opt/conda/bin/conda install -n tts -c conda-forge ffmpeg || \
    (add-apt-repository -y ppa:jonathonf/ffmpeg-4 && \
    apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    apt-get clean && rm -rf /var/lib/apt/lists/*)

# Install Rust toolchain
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | bash -s -- -y && \
    echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> /etc/profile.d/rust.sh && \
    chmod +x /etc/profile.d/rust.sh && \
    . $HOME/.cargo/env && \
    rustup default stable && \
    rustup update
