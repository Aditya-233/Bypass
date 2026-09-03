#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${SCRIPT_DIR}/bin"
SRC_DIR="${SCRIPT_DIR}/engine_src"

mkdir -p "${BIN_DIR}"
echo "Compiling native bypass-engine..."
gcc -std=c99 -O2 -Wall -Wextra -Wno-unused-parameter -D_DEFAULT_SOURCE \
    -I"${SRC_DIR}" \
    -o "${BIN_DIR}/bypass-engine" \
    "${SRC_DIR}/packets.c" \
    "${SRC_DIR}/main.c" \
    "${SRC_DIR}/conev.c" \
    "${SRC_DIR}/proxy.c" \
    "${SRC_DIR}/desync.c" \
    "${SRC_DIR}/mpool.c" \
    "${SRC_DIR}/extend.c"
chmod +x "${BIN_DIR}/bypass-engine"
echo "Build complete: ${BIN_DIR}/bypass-engine"
