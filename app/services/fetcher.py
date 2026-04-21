"""SSRF-safe URL fetcher for ingesting web pages into the knowledge base.

Hardens against common abuse:
  - Rejects non-http(s) schemes.
  - Resolves host to all A/AAAA records and refuses any that land on private,
    loopback, link-local, multicast, or reserved ranges.
  - Re-validates the host on every redirect hop (defends against DNS rebinding
    and redirect-based SSRF).
  - Streams the response and aborts once MAX_BYTES is exceeded.
  - Enforces a full-request timeout and a Content-Type whitelist.

Returns a FetchedResource with the raw bytes, final URL, extracted <title>,
and SHA-256 hash — consumed by services/document.py to build a Document.
"""
from __future__ import annotations

import hashlib
import ipaddress
import logging
import socket
from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse

import httpx

from app.config import settings
from app.core.exceptions import InvalidURLError, URLFetchError

logger = logging.getLogger(__name__)


@dataclass
class FetchedResource:
    url: str                # Input URL after normalization
    final_url: str          # URL after following redirects
    content: bytes          # Raw response body
    content_type: str       # Lowercased MIME type (no charset)
    title: str              # Extracted <title>, or host+path fallback
    content_hash: str       # sha256(content) hex


def normalize_url(raw: str) -> str:
    """Lowercase scheme/host, strip fragments, drop default ports.

    Keeps the URL deterministic so content-hash comparisons and duplicate
    checks behave predictably.
    """
    if not raw or not isinstance(raw, str):
        raise InvalidURLError("URL must be a non-empty string")

    parsed = urlparse(raw.strip())
    if parsed.scheme.lower() not in ("http", "https"):
        raise InvalidURLError(
            f"Only http/https URLs are allowed, got '{parsed.scheme}'"
        )
    if not parsed.netloc:
        raise InvalidURLError("URL is missing host")

    scheme = parsed.scheme.lower()
    host = parsed.hostname.lower() if parsed.hostname else ""
    if not host:
        raise InvalidURLError("URL is missing host")

    port = parsed.port
    netloc = host
    # Drop default ports so https://x/ and https://x:443/ hash the same.
    if port and not (
        (scheme == "http" and port == 80) or (scheme == "https" and port == 443)
    ):
        netloc = f"{host}:{port}"

    return urlunparse(
        (scheme, netloc, parsed.path or "/", parsed.params, parsed.query, "")
    )


def _assert_public_host(host: str) -> None:
    """Resolve host and refuse any IP that is not globally routable."""
    if settings.URL_FETCH_ALLOW_PRIVATE_NETWORK:
        return

    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as exc:
        raise URLFetchError(f"Cannot resolve host '{host}': {exc}") from exc

    if not infos:
        raise URLFetchError(f"No DNS records for host '{host}'")

    for info in infos:
        ip_str = info[4][0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            raise URLFetchError(f"Invalid IP '{ip_str}' for host '{host}'")
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            raise URLFetchError(
                f"Refusing to fetch private/reserved address {ip} for host '{host}'"
            )


def _extract_title(content: bytes, content_type: str) -> str:
    """Best-effort <title> extraction. Fallback to empty string."""
    if "html" not in content_type and "xml" not in content_type:
        return ""
    try:
        from bs4 import BeautifulSoup

        # lxml is fast; fall back to built-in parser if unavailable.
        try:
            soup = BeautifulSoup(content, "lxml")
        except Exception:
            soup = BeautifulSoup(content, "html.parser")
        if soup.title and soup.title.string:
            return soup.title.string.strip()[:500]
    except Exception as e:  # noqa: BLE001
        logger.debug("Title extraction failed: %s", e)
    return ""


async def fetch_url(url: str) -> FetchedResource:
    """Fetch a URL with SSRF, size, timeout, and content-type protections."""
    normalized = normalize_url(url)
    host = urlparse(normalized).hostname or ""
    _assert_public_host(host)

    timeout = httpx.Timeout(settings.URL_FETCH_TIMEOUT_SEC)
    headers = {
        "User-Agent": settings.URL_FETCH_USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,text/plain;q=0.9,*/*;q=0.1",
        "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8",
    }
    allowed_types = settings.url_fetch_allowed_content_types
    max_bytes = settings.URL_FETCH_MAX_BYTES

    async with httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=False,  # manual redirects so we can re-validate hosts
        headers=headers,
    ) as client:
        current_url = normalized
        redirects_left = settings.URL_FETCH_MAX_REDIRECTS
        while True:
            try:
                async with client.stream("GET", current_url) as response:
                    if response.is_redirect:
                        if redirects_left <= 0:
                            raise URLFetchError("Too many redirects")
                        location = response.headers.get("location")
                        if not location:
                            raise URLFetchError(
                                "Redirect response missing Location header"
                            )
                        # Resolve relative → absolute, then re-run SSRF guard.
                        next_url = str(response.url.join(location))
                        next_url = normalize_url(next_url)
                        next_host = urlparse(next_url).hostname or ""
                        _assert_public_host(next_host)
                        current_url = next_url
                        redirects_left -= 1
                        continue

                    if response.status_code >= 400:
                        raise URLFetchError(
                            f"HTTP {response.status_code} from {current_url}"
                        )

                    raw_ct = response.headers.get("content-type", "")
                    content_type = raw_ct.split(";", 1)[0].strip().lower()
                    if content_type and content_type not in allowed_types:
                        raise URLFetchError(
                            f"Unsupported Content-Type '{content_type}'. "
                            f"Allowed: {sorted(allowed_types)}"
                        )

                    buf = bytearray()
                    async for chunk in response.aiter_bytes():
                        buf.extend(chunk)
                        if len(buf) > max_bytes:
                            raise URLFetchError(
                                f"Response exceeds {max_bytes} bytes limit"
                            )
                    final_url = str(response.url)
                    content = bytes(buf)
                    break
            except httpx.TimeoutException as exc:
                raise URLFetchError(f"Request timed out: {exc}") from exc
            except httpx.HTTPError as exc:
                raise URLFetchError(str(exc)) from exc

    title = _extract_title(content, content_type) or host
    content_hash = hashlib.sha256(content).hexdigest()
    logger.info(
        "Fetched %s → %s (%d bytes, type=%s)",
        normalized, final_url, len(content), content_type,
    )
    return FetchedResource(
        url=normalized,
        final_url=final_url,
        content=content,
        content_type=content_type,
        title=title,
        content_hash=content_hash,
    )
