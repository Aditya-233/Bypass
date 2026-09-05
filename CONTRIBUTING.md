# Contributing to Bypass

We welcome contributions to Bypass! Whether it's adding new DPI evasion strategies, fixing bugs, or improving documentation, here's how you can help.

## Development Workflow

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Aditya-233/Bypass.git
   cd Bypass
   ```

2. **Build the native engine:**
   ```bash
   ./build.sh
   ```

3. **Install and test locally:**
   ```bash
   ./install.sh
   bypass start
   bypass test
   ```

4. **Code Quality & Linting:**
   Ensure all linters and type checkers pass without errors or warnings:
   ```bash
   # C Compiler checks
   gcc -std=c99 -Wall -Wextra -pedantic -Wno-unused-parameter -D_DEFAULT_SOURCE -Iengine_src -fsyntax-only engine_src/*.c

   # Shellcheck
   shellcheck -s bash build.sh install.sh

   # Python formatting and linting
   ruff check . bypass
   ruff format --check . bypass

   # Type checking
   basedpyright bypass bypass_http_proxy.py tests/test_bypass.py
   ```

5. **Run the integration test suite:**
   ```bash
   python3 tests/test_bypass.py
   ```

## Guidelines

- **BitTorrent Trackers**: Never strip or buffer raw tracker announcement packets in `bypass_http_proxy.py`.
- **Wire Speed Whitelist**: Ensure speed test domains in `speed_whitelist.txt` are preserved for native NIC speeds.
- **DNS Caching & IPv4**: Retain in-memory DNS caching and IPv4-first resolution (`-X`) to prevent IPv6 routing blackholes.
