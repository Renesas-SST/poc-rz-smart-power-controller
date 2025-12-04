#!/bin/sh
# SPDX-License-Identifier: BSD-4-Clause
# Copyright (c) 2025, Renesas Electronics America Inc
# This file is part of the project under the BSD 4-Clause License.

# Exit on error, unset variables, and pipe failures
set -e
set -u

# Print help message
show_help() {
    script_name=$(basename "$0")
    cat << EOF
build_deb.sh - Build a .deb package for RZ Smart Power Controller

Usage: 
    $script_name [options] [architecture]

Options:
    -h        Show this help message
    
Architecture:
    Specify the target architecture for the .deb package (default: arm64)
    
    Common values:
    - arm64        Package marked for ARM64 systems only (recommended)
    - all          Architecture-independent package (can install anywhere)
    - amd64        Package marked for x86_64 systems
    
    The architecture parameter affects package metadata only. Currently, this
    project contains only Python/shell scripts, so no cross-compilation occurs.
    Package contents are identical regardless of architecture chosen.

Examples:
    # Build for ARM64 (default)
    $script_name
    
    # Build architecture-independent package
    $script_name all
    
    # Show this help
    $script_name -h

Package inspection:
    After building, you can inspect the package:
    - View contents:    dpkg -c build/*.deb
    - View metadata:    dpkg -I build/*.deb
    - List files:      dpkg-deb -c build/*.deb
    
Notes:
        - The package installs under /usr/local by default
                - Python is required on the host and target. The helper `gpio_config_tool.py`
                    is included with the package and replaces the previous `jq` dependency.
        - Configure GPIO paths in src/gpio_config.json before building
EOF
}

# Parse command line
case ${1:-} in
    -h)
        show_help
        exit 0
        ;;
esac

# Default to arm64 if no architecture specified
ARCH=${1:-arm64}
ROOT_DIR=$(cd "$(dirname "$0")" && pwd)
BUILD_DIR="$ROOT_DIR/build"
SRC_DIR="$ROOT_DIR/src"

echo "Building .deb package for architecture: $ARCH"
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

# Prerequisites check (host)
missing=0
for cmd in cmake make cpack; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "Error: required command '$cmd' not found in PATH" >&2
        missing=1
    fi
done
if [ "$missing" -ne 0 ]; then
    echo "Please install the missing tools and re-run this script." >&2
    exit 2
fi

# Configure CMake with requested architecture
cmake -DCPACK_DEBIAN_PACKAGE_ARCHITECTURE="$ARCH" -DINSTALL_SYSTEMD_SERVICE=ON "$SRC_DIR"

# Build (no compilation but runs any install/generation steps)
if command -v nproc >/dev/null 2>&1; then
    JOBS=$(nproc)
else
    JOBS=1
fi
make -j"$JOBS"

# Create the .deb package
cpack -G DEB

echo "Build complete. Package location: $BUILD_DIR"
ls -l "$BUILD_DIR"/*.deb

# Show helpful next steps
cat << EOF

To check package contents:
  dpkg -c ${BUILD_DIR}/*.deb

To check package metadata (including architecture):
  dpkg -I ${BUILD_DIR}/*.deb

To install (when running on target hardware):
  sudo dpkg -i ${BUILD_DIR}/*.deb
  sudo apt-get -f install  # installs any missing dependencies
EOF