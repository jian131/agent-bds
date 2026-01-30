"""
Crawlers package - Real estate platform crawlers

Includes:
- Platform adapters for 10+ Vietnamese real estate sites
- Polite HTTP client with rate limiting
- Search orchestrator for parallel crawling
"""

from crawlers.adapters import (
    BasePlatformAdapter,
    PlatformRegistry,
    PlatformCapabilities,
    UnifiedListing,
    CrawlError,
    CrawlErrorType,
)
from crawlers.http_client import PoliteHttpClient
from crawlers.orchestrator import (
    SearchOrchestrator,
    SearchStatus,
    PlatformSearchResult,
    AggregatedSearchResult,
    get_orchestrator,
    search_all_platforms,
)

# Legacy imports for backward compatibility
try:
    from crawlers.base_crawler import BaseCrawler
    from crawlers.google_crawler import GoogleSearchCrawler
    from crawlers.platform_crawlers import PlatformCrawler
except ImportError:
    # These may not exist in the new structure
    BaseCrawler = None
    GoogleSearchCrawler = None
    PlatformCrawler = None

__all__ = [
    # New adapter system
    "BasePlatformAdapter",
    "PlatformRegistry",
    "PlatformCapabilities",
    "UnifiedListing",
    "CrawlError",
    "CrawlErrorType",
    "PoliteHttpClient",
    # Orchestrator
    "SearchOrchestrator",
    "SearchStatus",
    "PlatformSearchResult",
    "AggregatedSearchResult",
    "get_orchestrator",
    "search_all_platforms",
    # Legacy (if available)
    "BaseCrawler",
    "GoogleSearchCrawler",
    "PlatformCrawler",
]
