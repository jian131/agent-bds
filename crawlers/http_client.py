"""
HTTP Client with stealth features for bypassing anti-bot protection.

Features:
- Rotating User-Agents (real browser fingerprints)
- Browser-like headers
- Proxy support (HTTP/SOCKS5)
- Cookie persistence
- Rate limiting with jitter
- Automatic retry with backoff
"""

import asyncio
import random
import time
import os
from typing import Optional, Dict, Any, Tuple, List
from dataclasses import dataclass
from datetime import datetime, timedelta
from urllib.parse import urlparse, quote

import httpx
from cachetools import TTLCache

from core.logging import get_logger, CrawlLogger

logger = get_logger(__name__)


# Real browser User-Agents (updated 2024-2025)
USER_AGENTS = [
    # Chrome on Windows (most common)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    # Chrome on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    # Firefox on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    # Firefox on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) Gecko/20100101 Firefox/123.0",
    # Edge on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
    # Safari on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    # Mobile Chrome (for variety)
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Mobile/15E148 Safari/604.1",
]

# Browser-like headers for HTML pages
BROWSER_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "cross-site",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
    "sec-ch-ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "Pragma": "no-cache",
}

# API-specific headers (for JSON endpoints)
API_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "sec-ch-ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}


@dataclass
class RequestStats:
    """Statistics for a domain."""
    request_count: int = 0
    error_count: int = 0
    success_count: int = 0
    last_request_time: float = 0
    blocked_until: Optional[datetime] = None
    consecutive_403s: int = 0
    last_user_agent: str = ""


@dataclass
class ProxyConfig:
    """Proxy configuration."""
    url: str  # http://user:pass@host:port or socks5://host:port
    enabled: bool = True

    @classmethod
    def from_env(cls) -> Optional["ProxyConfig"]:
        """Load proxy from environment variables."""
        proxy_url = os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY") or os.getenv("PROXY_URL")
        if proxy_url:
            return cls(url=proxy_url, enabled=True)
        return None


class PoliteHttpClient:
    """
    HTTP client with stealth features for bypassing anti-bot protection.

    Features:
    - Rotating User-Agents (real browser fingerprints)
    - Browser-like headers with sec-ch-ua
    - Proxy support (HTTP/SOCKS5)
    - Cookie persistence per domain
    - Per-domain rate limiting with jitter
    - Automatic retry with exponential backoff (5 retries for 403)
    - Referer chain simulation
    """

    def __init__(
        self,
        rate_limit_rpm: int = 15,  # Lower rate for stealth
        timeout_seconds: int = 30,
        max_retries: int = 5,  # More retries for anti-bot bypass
        cache_ttl_seconds: int = 300,
        enable_cache: bool = True,
        proxy: Optional[ProxyConfig] = None,
    ):
        self.rate_limit_rpm = rate_limit_rpm
        self.timeout = httpx.Timeout(timeout_seconds, connect=15.0)
        self.max_retries = max_retries
        self.enable_cache = enable_cache

        # Proxy configuration
        self.proxy = proxy or ProxyConfig.from_env()

        # Per-domain stats
        self._domain_stats: Dict[str, RequestStats] = {}

        # Per-domain cookies
        self._cookies: Dict[str, httpx.Cookies] = {}

        # Response cache
        self._cache: TTLCache = TTLCache(maxsize=1000, ttl=cache_ttl_seconds)

        # Semaphore for concurrent request limiting
        self._semaphore = asyncio.Semaphore(3)  # Lower concurrency for stealth

        # Track last referer per domain
        self._last_referer: Dict[str, str] = {}

    def _get_domain(self, url: str) -> str:
        """Extract domain from URL."""
        return urlparse(url).netloc

    def _get_base_url(self, url: str) -> str:
        """Get base URL (scheme + domain)."""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def _get_stats(self, domain: str) -> RequestStats:
        """Get or create stats for domain."""
        if domain not in self._domain_stats:
            self._domain_stats[domain] = RequestStats()
        return self._domain_stats[domain]

    def _get_cookies(self, domain: str) -> httpx.Cookies:
        """Get or create cookie jar for domain."""
        if domain not in self._cookies:
            self._cookies[domain] = httpx.Cookies()
        return self._cookies[domain]

    def _encode_url(self, url: str) -> str:
        """
        Properly encode URL to handle Vietnamese characters.
        Keeps scheme, netloc, and path structure intact.
        """
        from urllib.parse import urlsplit, urlunsplit, quote

        try:
            # Split URL into components
            parts = urlsplit(url)

            # Encode path (handles Vietnamese chars)
            # safe='/:?=&' keeps URL structure intact
            encoded_path = quote(parts.path, safe='/:')
            encoded_query = quote(parts.query, safe='=&')

            # Reconstruct URL with encoded parts
            encoded_url = urlunsplit((
                parts.scheme,
                parts.netloc,
                encoded_path,
                encoded_query,
                parts.fragment
            ))

            return encoded_url

        except Exception as e:
            logger.warning("url_encode_failed", url=url[:100], error=str(e))
            return url  # Return original if encoding fails

    def _get_random_user_agent(self) -> str:
        """Get a random User-Agent."""
        return random.choice(USER_AGENTS)

    def _get_headers(self, url: str, is_api: bool = False) -> Dict[str, str]:
        """Get browser-like headers for request."""
        domain = self._get_domain(url)
        stats = self._get_stats(domain)

        # Rotate User-Agent occasionally (not every request - more realistic)
        if not stats.last_user_agent or random.random() < 0.15:
            stats.last_user_agent = self._get_random_user_agent()

        # Choose header template
        base_headers = API_HEADERS.copy() if is_api else BROWSER_HEADERS.copy()

        headers = {
            "User-Agent": stats.last_user_agent,
            **base_headers,
        }

        # Add realistic referer
        if domain in self._last_referer:
            headers["Referer"] = self._last_referer[domain]
        else:
            # First visit - use Google as referer (organic traffic simulation)
            headers["Referer"] = "https://www.google.com/"

        # Add origin for same-origin requests
        headers["Origin"] = self._get_base_url(url)

        return headers

    async def _wait_for_rate_limit(self, domain: str) -> None:
        """Wait to respect rate limit for domain with human-like jitter."""
        stats = self._get_stats(domain)

        if self.rate_limit_rpm <= 0:
            return

        min_interval = 60.0 / self.rate_limit_rpm
        elapsed = time.time() - stats.last_request_time

        if elapsed < min_interval:
            wait_time = min_interval - elapsed
            # Add human-like jitter (0.8x to 2.0x) - more variance
            jitter = random.uniform(0.8, 2.0)
            wait_time *= jitter
            # Add small random delay to simulate human behavior
            wait_time += random.uniform(0.3, 1.5)
            await asyncio.sleep(wait_time)

        stats.last_request_time = time.time()
        stats.request_count += 1

    def _is_blocked(self, domain: str) -> bool:
        """Check if domain is currently blocked."""
        stats = self._get_stats(domain)
        if stats.blocked_until and datetime.utcnow() < stats.blocked_until:
            return True
        return False

    def _mark_blocked(self, domain: str, duration_seconds: int = 300) -> None:
        """Mark domain as blocked for duration."""
        stats = self._get_stats(domain)
        stats.blocked_until = datetime.utcnow() + timedelta(seconds=duration_seconds)
        stats.consecutive_403s += 1
        stats.error_count += 1

        # Rotate User-Agent after block
        stats.last_user_agent = self._get_random_user_agent()

    def _mark_success(self, domain: str) -> None:
        """Mark successful request."""
        stats = self._get_stats(domain)
        stats.consecutive_403s = 0
        stats.blocked_until = None
        stats.success_count += 1

    def _get_proxy_config(self) -> Optional[str]:
        """Get proxy URL if configured."""
        if self.proxy and self.proxy.enabled:
            return self.proxy.url
        return None

    async def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        follow_redirects: bool = True,
        use_cache: bool = True,
        is_api: bool = False,
    ) -> Tuple[Optional[str], Optional[int], Optional[str]]:
        """
        Fetch URL with stealth crawling.

        Args:
            url: URL to fetch
            headers: Additional headers (merged with default)
            follow_redirects: Whether to follow redirects
            use_cache: Whether to use response cache
            is_api: Whether this is an API request (uses different headers)

        Returns:
            Tuple of (html_content, status_code, error_message)
        """
        # Encode URL to handle Vietnamese characters
        encoded_url = self._encode_url(url)

        domain = self._get_domain(encoded_url)
        crawl_logger = CrawlLogger(domain)

        # Check cache first
        if use_cache and self.enable_cache and encoded_url in self._cache:
            logger.debug("cache_hit", url=encoded_url)
            return self._cache[encoded_url], 200, None

        # Check if domain is blocked (with reduced block time on retry)
        if self._is_blocked(domain):
            stats = self._get_stats(domain)
            # Allow retry sooner if we have a proxy
            if self.proxy and self.proxy.enabled:
                stats.blocked_until = None  # Clear block if using proxy
            else:
                return None, 403, f"Domain {domain} is temporarily blocked"

        # Rate limiting with human-like delays
        await self._wait_for_rate_limit(domain)

        # Build headers
        request_headers = self._get_headers(encoded_url, is_api=is_api)
        if headers:
            request_headers.update(headers)

        # Get cookies for domain
        cookies = self._get_cookies(domain)

        # Get proxy
        proxy_url = self._get_proxy_config()

        start_time = time.time()

        async with self._semaphore:
            for attempt in range(self.max_retries):
                try:
                    # Create client with proxy if configured
                    client_kwargs = {
                        "timeout": self.timeout,
                        "follow_redirects": follow_redirects,
                        "cookies": cookies,
                        "verify": False,  # Skip SSL for some sites
                    }

                    if proxy_url:
                        client_kwargs["proxies"] = proxy_url

                    async with httpx.AsyncClient(**client_kwargs) as client:
                        # Add small random delay before request (human-like)
                        await asyncio.sleep(random.uniform(0.1, 0.4))

                        response = await client.get(encoded_url, headers=request_headers)
                        latency_ms = (time.time() - start_time) * 1000

                        # Store cookies from response
                        cookies.update(response.cookies)

                        # Update referer for next request
                        self._last_referer[domain] = encoded_url

                        # Handle specific status codes
                        if response.status_code == 200:
                            self._mark_success(domain)
                            html = response.text

                            # Cache successful response
                            if use_cache and self.enable_cache:
                                self._cache[encoded_url] = html

                            crawl_logger.crawl_success(encoded_url, 1, latency_ms)
                            return html, 200, None

                        elif response.status_code == 403:
                            # Try with completely different headers on retry
                            stats = self._get_stats(domain)
                            stats.last_user_agent = self._get_random_user_agent()

                            # Clear cookies and rebuild headers for fresh session
                            self._cookies[domain] = httpx.Cookies()
                            request_headers = self._get_headers(encoded_url, is_api=is_api)
                            if headers:
                                request_headers.update(headers)

                            if attempt < self.max_retries - 1:
                                # Longer exponential backoff with more jitter for 403
                                backoff = (2 ** attempt) * random.uniform(3.0, 6.0) + random.uniform(1.0, 3.0)
                                logger.warning(
                                    "403_retry",
                                    url=encoded_url,
                                    attempt=attempt + 1,
                                    max_retries=self.max_retries,
                                    backoff=round(backoff, 1),
                                    new_ua=stats.last_user_agent[:50],
                                )
                                await asyncio.sleep(backoff)
                                continue

                            self._mark_blocked(domain, 60)  # Short block, allow retry soon
                            crawl_logger.crawl_blocked(encoded_url, 403)
                            return None, 403, "Access forbidden - site blocks automated access"

                        elif response.status_code == 429:
                            # Rate limited - get Retry-After if available
                            retry_after = int(response.headers.get("Retry-After", 60))
                            self._mark_blocked(domain, retry_after)
                            crawl_logger.rate_limited(encoded_url, retry_after)
                            return None, 429, f"Rate limited - retry after {retry_after}s"

                        elif response.status_code == 404:
                            return None, 404, "Page not found"

                        elif response.status_code >= 500:
                            # Server error - retry with backoff
                            if attempt < self.max_retries - 1:
                                backoff = (2 ** attempt) * random.uniform(1.0, 2.0)
                                await asyncio.sleep(backoff)
                                continue
                            return None, response.status_code, f"Server error: {response.status_code}"

                        else:
                            return None, response.status_code, f"Unexpected status: {response.status_code}"

                except httpx.TimeoutException:
                    if attempt < self.max_retries - 1:
                        backoff = (2 ** attempt) * random.uniform(1.0, 2.0)
                        await asyncio.sleep(backoff)
                        continue
                    crawl_logger.crawl_error(encoded_url, "timeout", "Request timed out")
                    return None, None, "Request timed out"

                except httpx.ConnectError as e:
                    if attempt < self.max_retries - 1:
                        backoff = (2 ** attempt) * random.uniform(1.0, 2.0)
                        await asyncio.sleep(backoff)
                        continue
                    crawl_logger.crawl_error(encoded_url, "network_error", str(e))
                    return None, None, f"Connection error: {e}"

                except httpx.ProxyError as e:
                    logger.error("proxy_error", url=encoded_url, error=str(e))
                    # Disable proxy and retry without it
                    if self.proxy:
                        self.proxy.enabled = False
                    if attempt < self.max_retries - 1:
                        continue
                    return None, None, f"Proxy error: {e}"

                except Exception as e:
                    crawl_logger.crawl_error(encoded_url, "unknown", str(e))
                    return None, None, f"Unexpected error: {e}"

        return None, None, "Max retries exceeded"

    async def get_many(
        self,
        urls: List[str],
        max_concurrent: int = 3,
    ) -> List[Tuple[str, Optional[str], Optional[int], Optional[str]]]:
        """
        Fetch multiple URLs concurrently with rate limiting.

        Returns:
            List of (url, html, status_code, error) tuples
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def fetch_one(url: str):
            async with semaphore:
                html, status, error = await self.get(url)
                return url, html, status, error

        results = await asyncio.gather(
            *[fetch_one(url) for url in urls],
            return_exceptions=True
        )

        processed = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed.append((urls[i], None, None, str(result)))
            else:
                processed.append(result)

        return processed

    def get_domain_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get stats for all domains."""
        return {
            domain: {
                "request_count": stats.request_count,
                "success_count": stats.success_count,
                "error_count": stats.error_count,
                "consecutive_403s": stats.consecutive_403s,
                "blocked": self._is_blocked(domain),
                "blocked_until": stats.blocked_until.isoformat() if stats.blocked_until else None,
                "last_user_agent": stats.last_user_agent[:50] + "..." if len(stats.last_user_agent) > 50 else stats.last_user_agent,
            }
            for domain, stats in self._domain_stats.items()
        }

    def clear_blocks(self) -> None:
        """Clear all domain blocks."""
        for stats in self._domain_stats.values():
            stats.blocked_until = None
            stats.consecutive_403s = 0

    def clear_cookies(self, domain: Optional[str] = None) -> None:
        """Clear cookies for domain or all domains."""
        if domain:
            if domain in self._cookies:
                self._cookies[domain] = httpx.Cookies()
        else:
            self._cookies.clear()

    def set_proxy(self, proxy_url: str) -> None:
        """Set proxy URL."""
        self.proxy = ProxyConfig(url=proxy_url, enabled=True)
        logger.info("proxy_configured", proxy=proxy_url[:30] + "...")

    def disable_proxy(self) -> None:
        """Disable proxy."""
        if self.proxy:
            self.proxy.enabled = False


# Alias for backward compatibility
StealthHttpClient = PoliteHttpClient


# Global client instance
_http_client: Optional[PoliteHttpClient] = None


def get_http_client() -> PoliteHttpClient:
    """Get or create global HTTP client."""
    global _http_client
    if _http_client is None:
        _http_client = PoliteHttpClient()
    return _http_client


def configure_proxy(proxy_url: str) -> None:
    """Configure proxy for global HTTP client."""
    client = get_http_client()
    client.set_proxy(proxy_url)
