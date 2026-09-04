#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${SCRIPT_DIR}/bin"
INSTALL_TARGET="${HOME}/.local/bin/bypass"

echo "=================================================="
echo "    Installing Bypass DPI Circumvention Suite"
echo "=================================================="

# 1. Check Python 3
if ! command -v python3 &>/dev/null; then
    echo "[-] Error: python3 is required but not installed."
    echo "    Please install python3 using your package manager."
    exit 1
fi

# 2. Setup engine binary
if [[ -x "${BIN_DIR}/bypass-engine" ]]; then
    echo "[✓] Using pre-compiled native bypass-engine."
elif [[ -f "${SCRIPT_DIR}/build.sh" ]] && command -v gcc &>/dev/null; then
    echo "[*] Compiling native bypass-engine..."
    "${SCRIPT_DIR}/build.sh"
else
    echo "[-] Warning: ${BIN_DIR}/bypass-engine not found and gcc is unavailable."
fi

# 3. Make CLI scripts executable
chmod +x "${SCRIPT_DIR}/bypass"
chmod +x "${SCRIPT_DIR}/bypass_http_proxy.py"
[[ -f "${BIN_DIR}/bypass-engine" ]] && chmod +x "${BIN_DIR}/bypass-engine"

# 4. Create symlink in ~/.local/bin
mkdir -p "${HOME}/.local/bin"
ln -sf "${SCRIPT_DIR}/bypass" "${INSTALL_TARGET}"

echo ""
echo "[✓] Successfully installed 'bypass' to ${INSTALL_TARGET}"

# 5. Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":${HOME}/.local/bin:"* ]]; then
    echo ""
    echo "[!] Notice: ~/.local/bin is not currently in your PATH."
    echo "    To run 'bypass' from anywhere, add this to your ~/.bashrc or ~/.zshrc:"
    echo '    export PATH="$HOME/.local/bin:$PATH"'
    echo "    Or run directly: ${INSTALL_TARGET} start"
fi

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
