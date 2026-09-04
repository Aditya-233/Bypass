# Developer & Agent Guidelines: Bypass

This document guides human developers and future AI agents working on **Bypass**.

---

## 1. Project Purpose

Bypass provides DPI (Deep Packet Inspection) evasion and proxying so tools like Torrenty, package managers, and browsers can access blocked domains (Nyaa, anime portals, torrent trackers, etc.) without losing line speed or breaking TCP connections.

---

## 2. Key Components

- **`engine_src/` / `bin/`**: The core C DPI evasion engine utilizing raw sockets / nfqueue / TCP desync techniques (TTL trickery, fake requests, segment splitting).
- **`bypass_http_proxy.py`**: Local Python HTTP/HTTPS proxy (port 8080) and SOCKS5 proxy (port 1080) handling DNS caching, TCP desync for BitTorrent HTTP trackers, and proxy socket bridging.
- **`speed_whitelist.txt`**: Host whitelist (e.g. Netflix/Fast.com, Ookla) that bypasses DPI inspection to allow full wire-speed downloads (>500 Mbps).
- **`install.sh` / `build.sh`**: Installs `bypass` binary into user PATH (`/home/aditya/.local/bin` or system).

---

## 3. Critical Rules for Future Agents

1. **BitTorrent Tracker Compatibility**:
   - HTTP/HTTPS BitTorrent trackers require Out-Of-Band (OOB) TCP desync and transparent socket bridging. Never strip or buffer raw tracker announcement packets in the proxy.
2. **DNS Caching & IPv4-Only Mode**:
   - Always retain in-memory DNS caching and IPv4-first/only resolution (`-X`) to prevent IPv6 routing blackholes common with blocked ISPs.
3. **Line Speed & Whitelist**:
   - When evaluating throughput, ensure speed test domains in `speed_whitelist.txt` are preserved so CDN/streaming traffic operates at native NIC speeds.
