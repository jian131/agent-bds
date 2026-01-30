"""
Search Orchestrator

Coordinates parallel crawling across multiple platforms with:
- Semaphore-based concurrency limiting
- Per-platform rate limiting
- Graceful degradation on failures
- Result aggregation and deduplication
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum

from crawlers.adapters import (
    PlatformRegistry,
    UnifiedListing,
    CrawlError,
    CrawlErrorType,
    BlockedError,
    RateLimitError,
)
from crawlers.http_client import PoliteHttpClient
from core.logging import CrawlLogger, get_logger

logger = get_logger(__name__)


class SearchStatus(str, Enum):
    """Status of a platform search"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    PARTIAL = "partial"  # Some results but with errors
    BLOCKED = "blocked"
    ERROR = "error"
    TIMEOUT = "timeout"


@dataclass
class PlatformSearchResult:
    """Result from a single platform search"""
    platform_id: str
    platform_name: str
    status: SearchStatus
    listings: list[UnifiedListing] = field(default_factory=list)
    error: Optional[str] = None
    error_type: Optional[CrawlErrorType] = None
    duration_ms: int = 0
    url_attempted: Optional[str] = None


@dataclass
class AggregatedSearchResult:
    """Aggregated results from all platforms"""
    query: str
    total_listings: int
    platforms_searched: int
    platforms_successful: int
    platforms_blocked: int
    platforms_error: int
    listings: list[UnifiedListing]
    platform_results: list[PlatformSearchResult]
    search_duration_ms: int
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert to dictionary for API response"""
        return {
            "query": self.query,
            "total_listings": self.total_listings,
            "platforms_searched": self.platforms_searched,
            "platforms_successful": self.platforms_successful,
            "platforms_blocked": self.platforms_blocked,
            "platforms_error": self.platforms_error,
            "search_duration_ms": self.search_duration_ms,
            "timestamp": self.timestamp.isoformat(),
            "platform_status": [
                {
                    "platform_id": r.platform_id,
                    "platform_name": r.platform_name,
                    "status": r.status.value,
                    "count": len(r.listings),
                    "error": r.error,
                    "duration_ms": r.duration_ms,
                }
                for r in self.platform_results
            ],
            "listings": [
                {
                    "id": l.id,
                    "platform": l.platform,
                    "title": l.title,
                    "price": l.price,
                    "price_text": l.price_text,
                    "area": l.area,
                    "area_text": l.area_text,
                    "city": l.city,
                    "district": l.district,
                    "address": l.address,
                    "url": l.url,
                    "image_url": l.image_url,
                    "bedrooms": l.bedrooms,
                    "bathrooms": l.bathrooms,
                }
                for l in self.listings
            ],
        }


class SearchOrchestrator:
    """
    Orchestrates parallel searches across multiple real estate platforms.

    Features:
    - Concurrent requests with semaphore limiting
    - Per-platform rate limiting via PoliteHttpClient
    - Graceful degradation (continues if some platforms fail)
    - Result deduplication
    - Structured logging with trace_id
    """

    def __init__(
        self,
        max_concurrent: int = 5,
        timeout_seconds: float = 30.0,
        platforms: Optional[list[str]] = None,
    ):
        """
        Initialize orchestrator.

        Args:
            max_concurrent: Maximum concurrent platform requests
            timeout_seconds: Timeout per platform request
            platforms: List of platform IDs to search, or None for all
        """
        self.max_concurrent = max_concurrent
        self.timeout_seconds = timeout_seconds
        self.enabled_platforms = platforms
        self.http_client = PoliteHttpClient()
        self.logger = CrawlLogger(platform="orchestrator")
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def search(
        self,
        query: str,
        city: Optional[str] = None,
        district: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_area: Optional[float] = None,
        max_area: Optional[float] = None,
        page: int = 1,
    ) -> AggregatedSearchResult:
        """
        Execute parallel search across all enabled platforms.

        Args:
            query: Search query text
            city: Filter by city
            district: Filter by district
            min_price: Minimum price in VND
            max_price: Maximum price in VND
            min_area: Minimum area in m²
            max_area: Maximum area in m²
            page: Page number for pagination

        Returns:
            AggregatedSearchResult with listings from all platforms
        """
        start_time = datetime.utcnow()

        self.logger.info(
            "Starting multi-platform search",
            query=query,
            city=city,
            page=page,
        )

        # Get registered platforms
        all_platforms = PlatformRegistry.get_all()

        # Filter to enabled platforms if specified
        if self.enabled_platforms:
            platforms = {
                pid: adapter
                for pid, adapter in all_platforms.items()
                if pid in self.enabled_platforms
            }
        else:
            platforms = all_platforms

        if not platforms:
            self.logger.warning("No platforms available for search")
            return AggregatedSearchResult(
                query=query,
                total_listings=0,
                platforms_searched=0,
                platforms_successful=0,
                platforms_blocked=0,
                platforms_error=0,
                listings=[],
                platform_results=[],
                search_duration_ms=0,
            )

        # Build search params
        search_params = {
            "query": query,
            "city": city,
            "district": district,
            "min_price": min_price,
            "max_price": max_price,
            "min_area": min_area,
            "max_area": max_area,
            "page": page,
        }

        # Create tasks for parallel execution
        tasks = [
            self._search_platform(platform_id, adapter, search_params)
            for platform_id, adapter in platforms.items()
        ]

        # Execute all searches concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        platform_results: list[PlatformSearchResult] = []
        all_listings: list[UnifiedListing] = []

        for result in results:
            if isinstance(result, Exception):
                # This shouldn't happen as we handle exceptions in _search_platform
                self.logger.error(f"Unexpected exception in gather: {result}")
                continue

            platform_results.append(result)
            all_listings.extend(result.listings)

        # Deduplicate listings by normalized title + price
        deduplicated = self._deduplicate_listings(all_listings)

        # Calculate statistics
        end_time = datetime.utcnow()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        successful = sum(1 for r in platform_results if r.status == SearchStatus.SUCCESS)
        blocked = sum(1 for r in platform_results if r.status == SearchStatus.BLOCKED)
        errored = sum(1 for r in platform_results if r.status in [SearchStatus.ERROR, SearchStatus.TIMEOUT])

        self.logger.info(
            "Search completed",
            total_listings=len(deduplicated),
            platforms_searched=len(platform_results),
            platforms_successful=successful,
            platforms_blocked=blocked,
            duration_ms=duration_ms,
        )

        return AggregatedSearchResult(
            query=query,
            total_listings=len(deduplicated),
            platforms_searched=len(platform_results),
            platforms_successful=successful,
            platforms_blocked=blocked,
            platforms_error=errored,
            listings=deduplicated,
            platform_results=platform_results,
            search_duration_ms=duration_ms,
        )

    async def _search_platform(
        self,
        platform_id: str,
        adapter,
        params: dict,
    ) -> PlatformSearchResult:
        """
        Search a single platform with rate limiting and error handling.
        """
        start_time = datetime.utcnow()
        platform_logger = CrawlLogger(platform=platform_id)

        async with self._semaphore:
            try:
                # Build search URL
                url = adapter.build_search_url(**params)

                platform_logger.info(
                    "Searching platform",
                    url=url,
                    params=params,
                )

                # Fetch with timeout
                result = await asyncio.wait_for(
                    self.http_client.get(url),
                    timeout=self.timeout_seconds,
                )

                # Unpack result tuple (html, status_code, error)
                html, status_code, error = result

                # Check for errors
                if error or not html:
                    if status_code == 403:
                        raise BlockedError(message=error or "Access forbidden", url=url, platform=platform_id, status_code=403)
                    elif status_code == 429:
                        raise RateLimitError(message=error or "Rate limited", url=url, platform=platform_id, status_code=429)
                    else:
                        raise CrawlError(
                            error_type=CrawlErrorType.NETWORK_ERROR,
                            message=error or f"HTTP {status_code}",
                            url=url,
                            platform=platform_id,
                            status_code=status_code
                        )

                # Check for API support (Chotot, Nhatot)
                if hasattr(adapter, 'parse_api_response') and adapter.capabilities.supports_api:
                    try:
                        # Try JSON first
                        import json
                        data = json.loads(html)
                        listings = adapter.parse_api_response(data)
                    except (json.JSONDecodeError, ValueError):
                        # Fall back to HTML parsing
                        listings = adapter.parse_search_results(html)
                else:
                    listings = adapter.parse_search_results(html)

                duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

                platform_logger.info(
                    "Platform search successful",
                    listings_found=len(listings),
                    duration_ms=duration_ms,
                )

                return PlatformSearchResult(
                    platform_id=platform_id,
                    platform_name=adapter.platform_name,
                    status=SearchStatus.SUCCESS,
                    listings=listings,
                    duration_ms=duration_ms,
                    url_attempted=url,
                )

            except asyncio.TimeoutError:
                duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                platform_logger.warning("Platform search timed out", duration_ms=duration_ms)

                return PlatformSearchResult(
                    platform_id=platform_id,
                    platform_name=adapter.platform_name,
                    status=SearchStatus.TIMEOUT,
                    error="Request timed out",
                    error_type=CrawlErrorType.TIMEOUT,
                    duration_ms=duration_ms,
                )

            except CrawlError as e:
                duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

                if e.error_type == CrawlErrorType.BLOCKED:
                    platform_logger.warning(
                        "Platform blocked request",
                        error=str(e),
                        status_code=e.status_code,
                    )
                    status = SearchStatus.BLOCKED
                else:
                    platform_logger.error(
                        "Platform search failed",
                        error=str(e),
                        error_type=e.error_type.value,
                    )
                    status = SearchStatus.ERROR

                return PlatformSearchResult(
                    platform_id=platform_id,
                    platform_name=adapter.platform_name,
                    status=status,
                    error=str(e),
                    error_type=e.error_type,
                    duration_ms=duration_ms,
                )

            except Exception as e:
                duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                platform_logger.error(
                    "Unexpected error during platform search",
                    error=str(e),
                    error_type=type(e).__name__,
                )

                return PlatformSearchResult(
                    platform_id=platform_id,
                    platform_name=adapter.platform_name,
                    status=SearchStatus.ERROR,
                    error=str(e),
                    error_type=CrawlErrorType.PARSE_ERROR,
                    duration_ms=duration_ms,
                )

    def _deduplicate_listings(
        self,
        listings: list[UnifiedListing],
    ) -> list[UnifiedListing]:
        """
        Deduplicate listings based on normalized title + price.
        Keeps first occurrence (typically from higher-priority platform).
        """
        seen: set[str] = set()
        unique: list[UnifiedListing] = []

        for listing in listings:
            # Create dedup key from normalized title + price
            title_norm = (listing.title or "").lower().strip()
            price_key = str(listing.price) if listing.price else ""
            dedup_key = f"{title_norm[:50]}|{price_key}"

            if dedup_key not in seen:
                seen.add(dedup_key)
                unique.append(listing)

        return unique

    async def close(self):
        """Close HTTP client connections"""
        await self.http_client.close()


# Singleton instance for use across the application
_orchestrator: Optional[SearchOrchestrator] = None


def get_orchestrator() -> SearchOrchestrator:
    """Get or create the singleton orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = SearchOrchestrator()
    return _orchestrator


async def search_all_platforms(
    query: str,
    city: Optional[str] = None,
    district: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_area: Optional[float] = None,
    max_area: Optional[float] = None,
    page: int = 1,
) -> AggregatedSearchResult:
    """
    Convenience function to search all platforms.

    Example:
        results = await search_all_platforms(
            query="nhà phố",
            city="Hanoi",
            min_price=3_000_000_000,  # 3 tỷ
            max_price=5_000_000_000,  # 5 tỷ
        )
    """
    orchestrator = get_orchestrator()
    return await orchestrator.search(
        query=query,
        city=city,
        district=district,
        min_price=min_price,
        max_price=max_price,
        min_area=min_area,
        max_area=max_area,
        page=page,
    )
