#!/usr/bin/env python3
"""
Automated unit and integration test suite for Bypass DPI circumvention tool.
"""

import unittest
import socket
import subprocess
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class TestBypass(unittest.TestCase):

    def test_01_socks5_port_open(self):
        """Test that SOCKS5 engine is listening on 127.0.0.1:1080 and handles handshake"""
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        try:
            s.connect(("127.0.0.1", 1080))
            s.sendall(b"\x05\x01\x00")
            resp = s.recv(2)
            self.assertEqual(resp, b"\x05\x00", "SOCKS5 server did not accept NO AUTH")
        finally:
            s.close()

    def test_02_http_proxy_port_open(self):
        """Test that HTTP CONNECT proxy is listening on 127.0.0.1:8080 and handles CONNECT"""
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        try:
            s.connect(("127.0.0.1", 8080))
            s.sendall(b"CONNECT github.com:443 HTTP/1.1\r\nHost: github.com:443\r\n\r\n")
            resp = s.recv(1024)
            self.assertTrue(resp.startswith(b"HTTP/1.1 200 Connection Established"), f"Unexpected HTTP proxy response: {resp[:50]}")
        finally:
            s.close()

    def test_03_nyaa_unblocked(self):
        """Test accessing nyaa.si through SOCKS5 proxy"""
        cmd = [
            "curl",
            "-x", "socks5h://127.0.0.1:1080",
            "-s", "-I", "-m", "10",
            "--retry", "2", "--retry-delay", "1",
            "-H", "User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
            "https://nyaa.si"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"curl failed with code {res.returncode}: {res.stderr}")
        self.assertIn("200", res.stdout.split("\n")[0], f"Expected HTTP 200 from nyaa.si, got {res.stdout[:100]}")

    def test_04_fitgirl_unblocked(self):
        """Test accessing fitgirl-repacks.site through SOCKS5 proxy"""
        cmd = [
            "curl",
            "-x", "socks5h://127.0.0.1:1080",
            "-s", "-I", "-m", "12",
            "--retry", "2", "--retry-delay", "1",
            "-H", "User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
            "https://fitgirl-repacks.site"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"curl failed with code {res.returncode}: {res.stderr}")
        self.assertIn("200", res.stdout.split("\n")[0], f"Expected HTTP 200 from fitgirl, got {res.stdout[:100]}")

    def test_05_bypass_run_wrapper(self):
        """Test 'bypass run' command execution with proxy env"""
        bypass_bin = BASE_DIR / "bypass"
        cmd = [
            str(bypass_bin), "run",
            "curl", "-s", "-I", "-m", "8", "https://www.reddit.com"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"bypass run failed: {res.stderr}")
        self.assertTrue("200" in res.stdout, f"HTTP 200 status not found in response header: {res.stdout}")

    def test_06_bypass_env(self):
        """Test 'bypass env' and 'bypass unenv' output syntax"""
        bypass_bin = BASE_DIR / "bypass"
        res = subprocess.run([str(bypass_bin), "env"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("http_proxy=http://127.0.0.1:8080", res.stdout)
        self.assertIn("https_proxy=http://127.0.0.1:8080", res.stdout)

        res_un = subprocess.run([str(bypass_bin), "unenv"], capture_output=True, text=True)
        self.assertEqual(res_un.returncode, 0)
        self.assertIn("unset http_proxy", res_un.stdout)

if __name__ == "__main__":
    unittest.main(verbosity=2)
