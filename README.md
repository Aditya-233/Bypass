# Bypass - Low-Level DPI Evasion & Censorship Circumvention Suite

[![CI](https://github.com/Aditya-233/Bypass/actions/workflows/ci.yml/badge.svg)](https://github.com/Aditya-233/Bypass/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Linux-lightgrey.svg)](https://www.kernel.org)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org)
[![C Standard](https://img.shields.io/badge/c-C99-green.svg)](https://en.wikipedia.org/wiki/C99)

A lightweight, high-performance network tool designed to bypass middlebox Deep Packet Inspection (DPI) firewalls (such as **Fortinet FortiGate**, enterprise UTMs, and Indian ISP filters) to restore access to blocked educational, open-source, and media resources including `nyaa.si`, `fitgirl-repacks.site`, `1337x.to`, `rutracker.org`, and others.

---

## 1. Problem Analysis & How the Bypass Works

### The Censorship Mechanism
1. **Network Environment**: Hosts behind institutional/ISP middleboxes (e.g., IIT BHU using Fortinet FortiGate hardware firewalls).
2. **DPI Filtering**: Middleboxes inspect the unencrypted **TLS ClientHello Server Name Indication (SNI)** field on outbound HTTPS connections (port 443).
3. **Block Behavior**:
   - For `nyaa.si`, middleboxes inject TCP `RST` packets immediately upon parsing the SNI.
   - For `fitgirl-repacks.site`, middleboxes perform TLS interception using an untrusted Fortinet CA certificate (`CN=FGT3KD3Z16800731`), returning a `403 Web Filter Violation` page.

### The Low-Level Solution: TCP Out-Of-Band (OOB) Desync
Standard DPI hardware engines inspect traffic at line-rate and rely on standard TCP sequence streams to parse TLS record headers (`0x16 0x03 0x01...`).
- When the first byte of the TLS ClientHello is transmitted with the **TCP Urgent Flag (`MSG_OOB`)** (split at offset 1 with `-s 1 -o 1`), the middlebox state machine fails to assemble the TLS record framing or drops inspection of the stream.
- The remote destination server's standard Linux TCP stack receives and reassembles the stream completely.
- As a result, connection to the real website is established directly without middlebox interception or certificate forgery.

---

## 2. Architecture Overview

The suite provides a dual-proxy architecture running in user space (no root/sudo required):

1. **Native C SOCKS5 DPI Engine (`bin/bypass-engine`)**:
   - High-throughput, non-blocking asynchronous event loop written in C99.
   - Listens on `127.0.0.1:1080` (SOCKS5).
   - Performs TCP Out-Of-Band (URG) desynchronization on outbound TLS connections.
   - Performs remote DNS resolution.

2. **HTTP CONNECT Proxy Forwarder (`bypass_http_proxy.py`)**:
   - High-concurrency Python 3 proxy server.
   - Listens on `127.0.0.1:8080` (HTTP).
   - Translates standard `HTTP CONNECT` and plain HTTP proxy requests into SOCKS5 connections.
   - Allows tools and applications that only support HTTP proxies (`http_proxy`/`https_proxy`) to seamlessly utilize the DPI bypass.

3. **Unified CLI Utility (`bypass`)**:
   - Simple management interface for service lifecycle, connectivity verification, application wrapping, and browser profiles.

---

## 3. Installation

Run the automated build and installation script:

```bash
git clone https://github.com/Aditya-233/Bypass.git
cd Bypass
./install.sh
```

This compiles `bin/bypass-engine` using `gcc` and creates a symlink at `~/.local/bin/bypass`.

---

## 4. Usage Guide

### Service Management
```bash
# Start bypass services in background (SOCKS5: 1080, HTTP: 8080)
bypass start

# Check service status, PIDs, and port bindings
bypass status

# Restart services
bypass restart

# Stop services
bypass stop
```

### Verification & Testing
Test connectivity to blocked sites directly through the active bypass:
```bash
bypass test
```
Example output:
```
Target Website                   HTTP Code        Latency    Result
------------------------------------------------------------------------
https://nyaa.si                  200 OK             936ms   UNBLOCKED (Success)
https://fitgirl-repacks.site     200 OK            1210ms   UNBLOCKED (Success)
https://1337x.to                 403 (Origin/WAF)    69ms   UNBLOCKED (DPI Bypassed)
https://thepiratebay.org         403 (Origin/WAF)   544ms   UNBLOCKED (DPI Bypassed)
https://rutracker.org            200 OK            3564ms   UNBLOCKED (Success)
https://www.reddit.com           200 OK             112ms   UNBLOCKED (Success)
https://github.com               200 OK             296ms   UNBLOCKED (Success)

[✓] Verification test completed.
```

### Running Commands Through Bypass
Wrap any command to route its network traffic through the bypass:
```bash
# Run curl
bypass run curl -I https://nyaa.si

# Run git clone
bypass run git clone <repo_url>

# Run pip / npm
bypass run pip install <package>
```

### Shell Environment Export
To configure all commands in your current terminal session to use the bypass:
```bash
eval $(bypass env)
```
To revert back:
```bash
eval $(bypass unenv)
```

### Web Browser Usage

#### Option A: Dedicated Firefox Profile (Zero-Config)
Launch Firefox with an isolated profile pre-configured to route all DNS and traffic through SOCKS5:
```bash
bypass browser
```

#### Option B: Manual Browser Configuration
- **Firefox**:
  - Settings -> Network Settings -> Manual proxy configuration
  - SOCKS Host: `127.0.0.1`, Port: `1080`, SOCKS v5
  - Check `Proxy DNS when using SOCKS v5`
- **Chrome / Chromium / Brave**:
  ```bash
  google-chrome --proxy-server="socks5://127.0.0.1:1080"
  # Or HTTP proxy:
  google-chrome --proxy-server="http://127.0.0.1:8080"
  ```

### Torrent Clients (qBittorrent / Transmission)
In qBittorrent:
- Tools -> Options -> Connection -> Proxy Server
- Type: `SOCKS5`
- Host: `127.0.0.1`, Port: `1080`
- Enable `Use proxy for peer connections`
- Enable `Use proxy for hostname lookups`

### Auto-Start on System Login (systemd)
```bash
# Enable and start user systemd service
bypass service install

# Disable user systemd service
bypass service uninstall
```

---

## 5. Automated Test Suite

Run unit and integration tests:
```bash
python3 tests/test_bypass.py
```
