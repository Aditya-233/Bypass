#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${SCRIPT_DIR}/bin"
INSTALL_TARGET="${HOME}/.local/bin/bypass"

echo "=================================================="
echo "    Installing Bypass DPI Circumvention Suite"
echo "=================================================="

# 1. Compile native engine
"${SCRIPT_DIR}/build.sh"

# 2. Make CLI scripts executable
chmod +x "${SCRIPT_DIR}/bypass"
chmod +x "${SCRIPT_DIR}/bypass_http_proxy.py"

# 3. Create symlink in ~/.local/bin
mkdir -p "${HOME}/.local/bin"
ln -sf "${SCRIPT_DIR}/bypass" "${INSTALL_TARGET}"

echo ""
echo "[✓] Successfully installed 'bypass' to ${INSTALL_TARGET}"
echo ""
echo "Quick Start Commands:"
echo "  bypass start          - Start SOCKS5 (1080) and HTTP (8080) bypass proxies"
echo "  bypass test           - Test reachability of blocked websites (nyaa.si, fitgirl, etc.)"
echo "  bypass browser        - Launch Firefox pre-configured with the proxy"
echo "  bypass run <cmd>      - Run any command routed through bypass (curl, git, pip, etc.)"
echo "  eval \$(bypass env)    - Export proxy environment variables to current shell"
echo "  bypass status         - View proxy status and port bindings"
echo "  bypass stop           - Stop all bypass background services"
echo "=================================================="
