"""Unit tests for scrape URL validation."""

import pytest

from packages.core.url_safety import UnsafeUrlError, validate_scrape_url


def test_validate_scrape_url_accepts_https_public_host(monkeypatch):
    monkeypatch.delenv("SCRAPE_URL_ALLOWLIST", raising=False)
    assert validate_scrape_url("https://lu.ma/demo-event").startswith("https://")


def test_validate_scrape_url_rejects_http(monkeypatch):
    monkeypatch.delenv("SCRAPE_URL_ALLOWLIST", raising=False)
    with pytest.raises(UnsafeUrlError):
        validate_scrape_url("http://lu.ma/demo-event")


def test_validate_scrape_url_rejects_localhost(monkeypatch):
    monkeypatch.delenv("SCRAPE_URL_ALLOWLIST", raising=False)
    with pytest.raises(UnsafeUrlError):
        validate_scrape_url("https://localhost/admin")


def test_validate_scrape_url_enforces_allowlist(monkeypatch):
    monkeypatch.setenv("SCRAPE_URL_ALLOWLIST", "lu.ma")
    validate_scrape_url("https://lu.ma/demo")
    with pytest.raises(UnsafeUrlError):
        validate_scrape_url("https://example.com/page")
