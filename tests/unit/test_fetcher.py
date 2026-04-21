"""Unit tests for the URL fetcher — SSRF guard, size/timeout, redirects.

External network is never touched: httpx is mocked via MockTransport.
"""
import pytest
from unittest.mock import patch

import httpx

from app.core.exceptions import InvalidURLError, URLFetchError
from app.services import fetcher
from app.services.fetcher import fetch_url, normalize_url

pytestmark = pytest.mark.unit


# ── URL normalization ────────────────────────────────────────────────────

class TestNormalizeURL:
    def test_lowercases_scheme_and_host(self):
        assert normalize_url("HTTPS://Example.COM/Path") == "https://example.com/Path"

    def test_strips_fragment(self):
        assert normalize_url("https://a.com/p#section") == "https://a.com/p"

    def test_drops_default_port(self):
        assert normalize_url("https://a.com:443/") == "https://a.com/"
        assert normalize_url("http://a.com:80/") == "http://a.com/"

    def test_keeps_non_default_port(self):
        assert normalize_url("https://a.com:8443/") == "https://a.com:8443/"

    def test_rejects_non_http(self):
        with pytest.raises(InvalidURLError):
            normalize_url("file:///etc/passwd")
        with pytest.raises(InvalidURLError):
            normalize_url("ftp://a.com/x")

    def test_rejects_empty(self):
        with pytest.raises(InvalidURLError):
            normalize_url("")

    def test_rejects_missing_host(self):
        with pytest.raises(InvalidURLError):
            normalize_url("http:///no-host")


# ── SSRF guard ────────────────────────────────────────────────────────────

class TestSSRFGuard:
    """_assert_public_host must reject private/loopback/reserved addresses."""

    @pytest.mark.parametrize(
        "ip",
        ["127.0.0.1", "10.1.2.3", "172.16.0.1", "192.168.1.1", "169.254.1.1", "::1"],
    )
    def test_rejects_private_ips(self, ip, monkeypatch):
        monkeypatch.setattr(
            "socket.getaddrinfo",
            lambda host, port, *a, **kw: [(None, None, None, None, (ip, 0))],
        )
        with pytest.raises(URLFetchError, match="private/reserved"):
            fetcher._assert_public_host("evil.test")

    def test_accepts_public_ip(self, monkeypatch):
        monkeypatch.setattr(
            "socket.getaddrinfo",
            lambda host, port, *a, **kw: [(None, None, None, None, ("8.8.8.8", 0))],
        )
        fetcher._assert_public_host("example.com")  # no raise

    def test_unresolvable_host_raises(self, monkeypatch):
        import socket as _socket

        def boom(*a, **kw):
            raise _socket.gaierror("nope")

        monkeypatch.setattr("socket.getaddrinfo", boom)
        with pytest.raises(URLFetchError, match="Cannot resolve"):
            fetcher._assert_public_host("does-not-exist.tld")

    def test_private_allowed_when_flag_set(self, monkeypatch):
        from app.config import settings

        monkeypatch.setattr(settings, "URL_FETCH_ALLOW_PRIVATE_NETWORK", True)
        monkeypatch.setattr(
            "socket.getaddrinfo",
            lambda host, port, *a, **kw: [(None, None, None, None, ("127.0.0.1", 0))],
        )
        fetcher._assert_public_host("localhost")  # no raise


# ── Fetching via mocked httpx transport ──────────────────────────────────

@pytest.fixture
def bypass_ssrf(monkeypatch):
    """Short-circuit DNS resolution so fetch tests can use arbitrary hostnames."""
    monkeypatch.setattr(fetcher, "_assert_public_host", lambda host: None)


def _mock_client(handler):
    """Patch AsyncClient so it uses a MockTransport wrapping `handler`."""
    original = httpx.AsyncClient

    def factory(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        return original(*args, **kwargs)

    return patch("app.services.fetcher.httpx.AsyncClient", factory)


@pytest.mark.asyncio
async def test_fetch_success(bypass_ssrf):
    html = (
        b"<html><head><title>Hello World</title></head>"
        b"<body><p>hi</p></body></html>"
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, content=html, headers={"content-type": "text/html; charset=utf-8"}
        )

    with _mock_client(handler):
        result = await fetch_url("https://example.com/a")

    assert result.content == html
    assert result.title == "Hello World"
    assert result.content_type == "text/html"
    assert result.content_hash  # sha256 hex
    assert len(result.content_hash) == 64


@pytest.mark.asyncio
async def test_fetch_rejects_disallowed_content_type(bypass_ssrf):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, content=b"%PDF-1.4", headers={"content-type": "application/pdf"}
        )

    with _mock_client(handler):
        with pytest.raises(URLFetchError, match="Unsupported Content-Type"):
            await fetch_url("https://example.com/file.pdf")


@pytest.mark.asyncio
async def test_fetch_size_limit(bypass_ssrf, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "URL_FETCH_MAX_BYTES", 100)

    big = b"x" * 500

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=big, headers={"content-type": "text/html"})

    with _mock_client(handler):
        with pytest.raises(URLFetchError, match="exceeds"):
            await fetch_url("https://example.com/big")


@pytest.mark.asyncio
async def test_fetch_http_error(bypass_ssrf):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, content=b"oops", headers={"content-type": "text/html"})

    with _mock_client(handler):
        with pytest.raises(URLFetchError, match="HTTP 500"):
            await fetch_url("https://example.com/err")


@pytest.mark.asyncio
async def test_fetch_follows_redirect_then_success(bypass_ssrf):
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        if request.url.path == "/old":
            return httpx.Response(
                301,
                headers={"location": "https://example.com/new"},
            )
        return httpx.Response(
            200,
            content=b"<html><title>Final</title></html>",
            headers={"content-type": "text/html"},
        )

    with _mock_client(handler):
        result = await fetch_url("https://example.com/old")

    assert result.title == "Final"
    assert any("/new" in c for c in calls)


@pytest.mark.asyncio
async def test_fetch_too_many_redirects(bypass_ssrf, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "URL_FETCH_MAX_REDIRECTS", 2)

    hop = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        hop["n"] += 1
        return httpx.Response(
            301, headers={"location": f"https://example.com/r{hop['n']}"}
        )

    with _mock_client(handler):
        with pytest.raises(URLFetchError, match="Too many redirects"):
            await fetch_url("https://example.com/start")


@pytest.mark.asyncio
async def test_fetch_redirect_to_private_rejected(monkeypatch):
    """Redirect target must be re-validated — private IPs still blocked."""
    from app.config import settings

    monkeypatch.setattr(settings, "URL_FETCH_ALLOW_PRIVATE_NETWORK", False)

    # First hop: public; redirect hop: private.
    def fake_resolve(host):
        if host == "public.test":
            return [(None, None, None, None, ("8.8.8.8", 0))]
        return [(None, None, None, None, ("127.0.0.1", 0))]

    monkeypatch.setattr("socket.getaddrinfo", lambda host, port=None, *a, **kw: fake_resolve(host))

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "public.test":
            return httpx.Response(
                301, headers={"location": "http://internal.test/admin"}
            )
        return httpx.Response(200, content=b"<html></html>", headers={"content-type": "text/html"})

    with _mock_client(handler):
        with pytest.raises(URLFetchError, match="private/reserved"):
            await fetch_url("https://public.test/")
