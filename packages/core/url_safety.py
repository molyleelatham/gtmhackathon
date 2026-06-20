"""Validate user-supplied URLs before server-side fetch (Playwright scrape)."""

from __future__ import annotations

import ipaddress
import os
from urllib.parse import urlparse


class UnsafeUrlError(ValueError):
    """Raised when a URL must not be fetched by the backend."""


def _hostname_allowed(host: str) -> bool:
    allowlist_raw = os.getenv("SCRAPE_URL_ALLOWLIST", "").strip()
    if not allowlist_raw:
        return True
    allowed = [part.strip().lower() for part in allowlist_raw.split(",") if part.strip()]
    host_lower = host.lower()
    return any(host_lower == entry or host_lower.endswith(f".{entry}") for entry in allowed)


def validate_scrape_url(url: str) -> str:
    """Return a normalized HTTPS URL or raise UnsafeUrlError."""
    raw = (url or "").strip()
    if not raw:
        raise UnsafeUrlError("directory_url is required")

    parsed = urlparse(raw)
    if parsed.scheme.lower() != "https":
        raise UnsafeUrlError("directory_url must use HTTPS")
    if parsed.username or parsed.password:
        raise UnsafeUrlError("directory_url must not include credentials")
    if parsed.fragment:
        raise UnsafeUrlError("directory_url must not include a fragment")

    host = (parsed.hostname or "").strip().lower()
    if not host:
        raise UnsafeUrlError("directory_url is missing a host")

    blocked_hosts = {"localhost", "127.0.0.1", "0.0.0.0", "::1", "metadata.google.internal"}
    if host in blocked_hosts or host.endswith(".local"):
        raise UnsafeUrlError("directory_url host is not allowed")

    try:
        ip = ipaddress.ip_address(host)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise UnsafeUrlError("directory_url must not target a private or reserved address")
    except ValueError:
        pass

    if not _hostname_allowed(host):
        raise UnsafeUrlError("directory_url host is not in SCRAPE_URL_ALLOWLIST")

    port = parsed.port
    if port is not None and port not in (443,):
        raise UnsafeUrlError("directory_url must use the default HTTPS port")

    return parsed.geturl()
