"""
Polite HTTP Client with rate limiting, retries, and backoff.
NO bypass techniques - compliant with site policies.
"""

import asyncio
import random
import time
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import lru_cache
from urllib.parse import urlparse

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
from cachetools import TTLCache

from core.logging import get_logger, CrawlLogger

logger = get_logger(__name__)


@dataclass
class RequestStats:
    """Statistics for a domain."""
    request_count: int = 0
    error_count: int = 0
    last_request_time: float = 0
    blocked_until: Optional[datetime] = None
    consecutive_403s: int = 0


class PoliteHttpClient:
    """
    HTTP client that respects rate limits and site policies.

    Features:
    - Per-domain rate limiting
    - Jittered exponential backoff
    - Automatic retry with configurable attempts
    - Request caching (optional)
    - Proper User-Agent identification
    - Graceful handling of 403/429 responses
    """

    # Identify as a bot - honest User-Agent
    USER_AGENT = "BDSAgent/2.1 (+https://github.com/jian131/agent-bds; real-estate-search-bot)"

    # Browser-like headers for sites that require it (still honest about being a bot)
    BROWSER_LIKE_HEADERS = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "DNT": "1",
    }

    def __init__(
        self,
        rate_limit_rpm: int = 30,
        timeout_seconds: int = 30,
        max_retries: int = 3,
        cache_ttl_seconds: int = 300,
        enable_cache: bool = True,
    ):
        self.rate_limit_rpm = rate_limit_rpm
        self.timeout = httpx.Timeout(timeout_seconds, connect=10.0)
        self.max_retries = max_retries
        self.enable_cache = enable_cache

        # Per-domain stats
        self._domain_stats: Dict[str, RequestStats] = {}

        # Response cache
        self._cache: TTLCache = TTLCache(maxsize=1000, ttl=cache_ttl_seconds)

        # Semaphore for concurrent request limiting
        self._semaphore = asyncio.Semaphore(5)

    def _get_domain(self, url: str) -> str:
        """Extract domain from URL."""
        return urlparse(url).netloc

    def _get_stats(self, domain: str) -> RequestStats:
        """Get or create stats for domain."""
        if domain not in self._domain_stats:
            self._domain_stats[domain] = RequestStats()
        return self._domain_stats[domain]

    async def _wait_for_rate_limit(self, domain: str) -> None:
        """Wait to respect rate limit for domain."""
        stats = self._get_stats(domain)

        if self.rate_limit_rpm <= 0:
            return

        min_interval = 60.0 / self.rate_limit_rpm
        elapsed = time.time() - stats.last_request_time

        if elapsed < min_interval:
            wait_time = min_interval - elapsed
            # Add jitter (0.5x to 1.5x)
            jitter = random.uniform(0.5, 1.5)
            wait_time *= jitter
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

    def _mark_success(self, domain: str) -> None:
        """Mark successful request."""
        stats = self._get_stats(domain)
        stats.consecutive_403s = 0
        stats.blocked_until = None

    def _get_headers(self, url: str) -> Dict[str, str]:
        """Get headers for request."""
        domain = self._get_domain(url)
        headers = {
            "User-Agent": self.USER_AGENT,
            **self.BROWSER_LIKE_HEADERS,
            "Referer": f"https://{domain}/",
        }
        return headers

    async def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        follow_redirects: bool = True,
        use_cache: bool = True,
    ) -> Tuple[Optional[str], Optional[int], Optional[str]]:
        """
        Fetch URL with polite crawling.

        Args:
            url: URL to fetch
            headers: Additional headers
            follow_redirects: Whether to follow redirects
            use_cache: Whether to use response cache

        Returns:
            Tuple of (html_content, status_code, error_message)
        """
        domain = self._get_domain(url)
        crawl_logger = CrawlLogger(domain)

        # Check cache first
        if use_cache and self.enable_cache and url in self._cache:
            logger.debug("cache_hit", url=url)
            return self._cache[url], 200, None

        # Check if domain is blocked
        if self._is_blocked(domain):
            return None, 403, f"Domain {domain} is temporarily blocked"

        # Rate limiting
        await self._wait_for_rate_limit(domain)

        # Merge headers
        request_headers = self._get_headers(url)
        if headers:
            request_headers.update(headers)

        start_time = time.time()

        async with self._semaphore:
            for attempt in range(self.max_retries):
                try:
                    async with httpx.AsyncClient(
                        timeout=self.timeout,
                        follow_redirects=follow_redirects,
                    ) as client:
                        response = await client.get(url, headers=request_headers)
                        latency_ms = (time.time() - start_time) * 1000

                        # Handle specific status codes
                        if response.status_code == 200:
                            self._mark_success(domain)
                            html = response.text

                            # Cache successful response
                            if use_cache and self.enable_cache:
                                self._cache[url] = html

                            crawl_logger.crawl_success(url, 1, latency_ms)
                            return html, 200, None

                        elif response.status_code == 403:
                            self._mark_blocked(domain, 300)  # Block for 5 minutes
                            crawl_logger.crawl_blocked(url, 403)
                            return None, 403, "Access forbidden - site blocks automated access"

                        elif response.status_code == 429:
                            # Rate limited - get Retry-After if available
                            retry_after = int(response.headers.get("Retry-After", 60))
                            self._mark_blocked(domain, retry_after)
                            crawl_logger.rate_limited(url, retry_after)
                            return None, 429, f"Rate limited - retry after {retry_after}s"

                        elif response.status_code == 404:
                            return None, 404, "Page not found"

                        elif response.status_code >= 500:
                            # Server error - retry with backoff
                            if attempt < self.max_retries - 1:
                                backoff = (2 ** attempt) * random.uniform(0.5, 1.5)
                                await asyncio.sleep(backoff)
                                continue
                            return None, response.status_code, f"Server error: {response.status_code}"

                        else:
                            return None, response.status_code, f"Unexpected status: {response.status_code}"

                except httpx.TimeoutException:
                    if attempt < self.max_retries - 1:
                        backoff = (2 ** attempt) * random.uniform(0.5, 1.5)
                        await asyncio.sleep(backoff)
                        continue
                    crawl_logger.crawl_error(url, "timeout", "Request timed out")
                    return None, None, "Request timed out"

                except httpx.ConnectError as e:
                    if attempt < self.max_retries - 1:
                        backoff = (2 ** attempt) * random.uniform(0.5, 1.5)
                        await asyncio.sleep(backoff)
                        continue
                    crawl_logger.crawl_error(url, "network_error", str(e))
                    return None, None, f"Connection error: {e}"

                except Exception as e:
                    crawl_logger.crawl_error(url, "unknown", str(e))
                    return None, None, f"Unexpected error: {e}"

        return None, None, "Max retries exceeded"

    async def get_many(
        self,
        urls: list[str],
        max_concurrent: int = 5,
    ) -> list[Tuple[str, Optional[str], Optional[int], Optional[str]]]:
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
                "error_count": stats.error_count,
                "consecutive_403s": stats.consecutive_403s,
                "blocked": self._is_blocked(domain),
                "blocked_until": stats.blocked_until.isoformat() if stats.blocked_until else None,
            }
            for domain, stats in self._domain_stats.items()
        }

    def clear_blocks(self) -> None:
        """Clear all domain blocks (for testing)."""
        for stats in self._domain_stats.values():
            stats.blocked_until = None
            stats.consecutive_403s = 0


# Global client instance
_http_client: Optional[PoliteHttpClient] = None


def get_http_client() -> PoliteHttpClient:
    """Get or create global HTTP client."""
    global _http_client
    if _http_client is None:
        _http_client = PoliteHttpClient()
    return _http_client
