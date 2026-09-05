#!/usr/bin/env python3
"""
High-performance HTTP/HTTPS CONNECT proxy forwarding to SOCKS5.
Allows tools that only support HTTP proxies to seamlessly use the DPI bypass engine.
"""

from __future__ import annotations

import argparse
import os
import socket
import sys
import threading
import urllib.parse

BUFFER_SIZE: int = 65536


def socks5_connect(
    socks_host: str, socks_port: int, dest_host: str, dest_port: int
) -> socket.socket:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    s.connect((socks_host, socks_port))

    # 1. Handshake: VER=5, NMETHODS=1, METHOD=0 (No auth)
    s.sendall(b"\x05\x01\x00")
    resp = s.recv(2)
    if len(resp) < 2 or resp[0] != 5 or resp[1] != 0:
        s.close()
        raise RuntimeError("SOCKS5 handshake failed (no auth rejected)")

    # 2. Request: VER=5, CMD=1 (CONNECT), RSV=0, ATYP=3 (DOMAINNAME), DOMAIN, PORT
    dest_bytes = dest_host.encode("utf-8")
    req = (
        b"\x05\x01\x00\x03"
        + bytes([len(dest_bytes)])
        + dest_bytes
        + dest_port.to_bytes(2, "big")
    )
    s.sendall(req)

    # Reply: VER, REP, RSV, ATYP, BND.ADDR, BND.PORT
    reply = s.recv(4)
    if len(reply) < 4 or reply[1] != 0:
        s.close()
        rep_code = reply[1] if len(reply) >= 2 else -1
        raise RuntimeError(f"SOCKS5 connect rejected with status code {rep_code}")

    # Consume rest of reply address
    atyp = reply[3]
    if atyp == 1:  # IPv4 (4 bytes) + port (2 bytes)
        _ = s.recv(6)
    elif atyp == 3:  # Domain (1 byte len + domain) + port (2 bytes)
        dlen = s.recv(1)[0]
        _ = s.recv(dlen + 2)
    elif atyp == 4:  # IPv6 (16 bytes) + port (2 bytes)
        _ = s.recv(18)

    return s


def pipe_data(src: socket.socket, dst: socket.socket) -> None:
    try:
        while True:
            data = src.recv(BUFFER_SIZE)
            if not data:
                break
            dst.sendall(data)
    except OSError:
        pass
    finally:
        try:
            _ = dst.shutdown(socket.SHUT_WR)
        except OSError:
            pass


def bridge_sockets(sock1: socket.socket, sock2: socket.socket) -> None:
    sock1.setblocking(True)
    sock2.setblocking(True)
    t1 = threading.Thread(target=pipe_data, args=(sock1, sock2), daemon=True)
    t2 = threading.Thread(target=pipe_data, args=(sock2, sock1), daemon=True)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    try:
        sock1.close()
    except OSError:
        pass
    try:
        sock2.close()
    except OSError:
        pass


def handle_client(client_sock: socket.socket, socks_host: str, socks_port: int) -> None:
    try:
        req_data = b""
        while b"\r\n\r\n" not in req_data:
            chunk = client_sock.recv(4096)
            if not chunk:
                client_sock.close()
                return
            req_data += chunk
            if len(req_data) > 65536:
                client_sock.close()
                return

        header_part, rest = req_data.split(b"\r\n\r\n", 1)
        lines = header_part.split(b"\r\n")
        first_line = lines[0].decode("utf-8", errors="ignore")
        parts = first_line.split(" ")
        if len(parts) < 2:
            client_sock.close()
            return

        method: str = parts[0].upper()
        target: str = parts[1]
        print(f"[HTTP-PROXY] {method} {target}", file=sys.stderr, flush=True)

        if method == "CONNECT":
            # HTTPS Tunneling
            if ":" in target:
                host, port_str = target.split(":", 1)
                port = int(port_str)
            else:
                host = target
                port = 443

            try:
                remote_sock = socks5_connect(socks_host, socks_port, host, port)
            except (OSError, RuntimeError) as e:
                client_sock.sendall(
                    b"HTTP/1.1 502 Bad Gateway\r\nContent-Type: text/plain\r\nConnection: close\r\n\r\n"
                    + str(e).encode()
                )
                client_sock.close()
                return

            client_sock.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
            if rest:
                remote_sock.sendall(rest)

            bridge_sockets(client_sock, remote_sock)

        else:
            # Plain HTTP Proxying
            parsed = urllib.parse.urlparse(target)
            host: str | None = parsed.hostname
            port: int = parsed.port or 80
            path: str = parsed.path or "/"
            if parsed.query:
                path += "?" + parsed.query

            if not host:
                for l in lines[1:]:
                    if l.lower().startswith(b"host:"):
                        h_val = (
                            l.split(b":", 1)[1].strip().decode("utf-8", errors="ignore")
                        )
                        if ":" in h_val:
                            host, p_str = h_val.split(":", 1)
                            port = int(p_str)
                        else:
                            host = h_val
                        break

            if (not host or host in ("127.0.0.1", "localhost")) and (
                b"/announce" in req_data or b"/scrape" in req_data
            ):
                host = "nyaa.tracker.wf"
                port = 7777

            if not host:
                client_sock.close()
                return

            try:
                if b"/announce" in req_data or b"/scrape" in req_data:
                    remote_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    remote_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                    remote_sock.connect((host, port))
                else:
                    remote_sock = socks5_connect(socks_host, socks_port, host, port)
            except (OSError, RuntimeError) as e:
                client_sock.sendall(
                    b"HTTP/1.1 502 Bad Gateway\r\nContent-Type: text/plain\r\nConnection: close\r\n\r\n"
                    + str(e).encode()
                )
                client_sock.close()
                return

            new_first_line = (
                f"{method} {path} {parts[2] if len(parts) > 2 else 'HTTP/1.1'}\r\n"
            )
            new_headers = new_first_line.encode("utf-8")
            for l in lines[1:]:
                if not l.lower().startswith(b"proxy-"):
                    new_headers += l + b"\r\n"
            new_headers += b"\r\n" + rest

            if b"/announce" in req_data or b"/scrape" in req_data:
                # Desync FortiGate DPI by sending first byte with TCP MSG_OOB!
                try:
                    _ = remote_sock.send(new_headers[:1], socket.MSG_OOB)
                except OSError:
                    pass

            remote_sock.sendall(new_headers)

            bridge_sockets(client_sock, remote_sock)

    except (OSError, RuntimeError):
        try:
            client_sock.close()
        except OSError:
            pass


def run_server(
    listen_ip: str,
    listen_port: int,
    socks_host: str,
    socks_port: int,
    pidfile: str | None = None,
) -> None:
    if pidfile:
        with open(pidfile, "w") as f:
            _ = f.write(str(os.getpid()))

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((listen_ip, listen_port))
    server.listen(128)

    while True:
        try:
            conn_res = server.accept()
            client: socket.socket = conn_res[0]
            client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            t = threading.Thread(
                target=handle_client, args=(client, socks_host, socks_port), daemon=True
            )
            t.start()
        except KeyboardInterrupt:
            break
        except OSError:
            continue


class ProxyArgs(argparse.Namespace):
    listen_ip: str = "127.0.0.1"
    listen_port: int = 8080
    socks_host: str = "127.0.0.1"
    socks_port: int = 1080
    pidfile: str | None = None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="HTTP to SOCKS5 forwarder for DPI bypass"
    )
    _ = parser.add_argument("--listen-ip", default="127.0.0.1")
    _ = parser.add_argument("--listen-port", type=int, default=8080)
    _ = parser.add_argument("--socks-host", default="127.0.0.1")
    _ = parser.add_argument("--socks-port", type=int, default=1080)
    _ = parser.add_argument("--pidfile", default=None)
    args: ProxyArgs = parser.parse_args(namespace=ProxyArgs())

    run_server(
        args.listen_ip,
        args.listen_port,
        args.socks_host,
        args.socks_port,
        args.pidfile,
    )
