#!/usr/bin/env bash
# Build the RP2350 firmware with the Pico SDK.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${ROOT_DIR}/firmware/build"

cmake -S "${ROOT_DIR}/firmware" -B "${BUILD_DIR}" -G Ninja \
    -DPICO_BOARD=pico2 \
    -DPICO_PLATFORM=rp2350-arm-s
cmake --build "${BUILD_DIR}"
