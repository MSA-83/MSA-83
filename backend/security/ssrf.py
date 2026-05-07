"""SSRF (Server-Side Request Forgery) protection."""

import ipaddress
import re
from urllib.parse import urlparse

BLOCKED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
    "metadata.google.internal",
    "169.254.169.254",
    "instance-data",
]

BLOCKED_SCHEMES = {"file", "gopher", "dict", "ftp", "data", "jar"}

PRIVATE_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fe80::/10"),
]

DNS_REBIND_PATTERN = re.compile(r"(?i)(nip\.io|sslip\.io|localtest\.me|lvh\.me)")


class SSRFProtector:
    """Protect against Server-Side Request Forgery attacks."""

    def __init__(self, allow_private: bool = False):
        self.allow_private = allow_private

    def validate_url(self, url: str) -> bool:
        """Validate that a URL is safe to fetch."""
        try:
            parsed = urlparse(url)
        except Exception:
            return False

        if parsed.scheme.lower() in BLOCKED_SCHEMES:
            return False

        if not parsed.hostname:
            return False

        hostname = parsed.hostname.lower()

        if DNS_REBIND_PATTERN.search(hostname):
            return False

        for blocked in BLOCKED_HOSTS:
            if hostname == blocked or hostname.endswith(f".{blocked}"):
                return False

        parts = hostname.split(".")
        for part in parts:
            if part in BLOCKED_HOSTS:
                return False

        for i in range(len(parts)):
            for j in range(i + 1, min(i + 5, len(parts) + 1)):
                candidate = ".".join(parts[i:j])
                if candidate in BLOCKED_HOSTS:
                    return False

        if self.allow_private:
            return True

        try:
            ip = ipaddress.ip_address(hostname)
            for network in PRIVATE_RANGES:
                if ip in network:
                    return False
        except ValueError:
            pass

        return True

    def validate_urls(self, urls: list[str]) -> dict[str, bool]:
        """Validate multiple URLs and return results."""
        return {url: self.validate_url(url) for url in urls}

    def safe_fetch_urls(self, urls: list[str]) -> list[str]:
        """Filter to only safe URLs."""
        return [url for url in urls if self.validate_url(url)]


ssrf_protector = SSRFProtector()
