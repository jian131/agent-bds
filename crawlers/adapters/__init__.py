"""
Platform adapters package.

Import all adapters to register them with PlatformRegistry.
"""

from crawlers.adapters.base import (
    BasePlatformAdapter,
    PlatformConfig,
    PlatformStatus,
    PlatformCapabilities,
    PlatformRegistry,
    platform_registry,
    UnifiedListing,
    CrawlError,
    CrawlErrorType,
)

# Import all platform adapters to trigger registration
from crawlers.adapters.batdongsan import BatDongSanAdapter
from crawlers.adapters.chotot import ChototAdapter
from crawlers.adapters.mogi import MogiAdapter
from crawlers.adapters.alonhadat import AlonhadatAdapter
from crawlers.adapters.nhadat24h import Nhadat24hAdapter
from crawlers.adapters.homedy import HomedyAdapter
from crawlers.adapters.muaban import MuabanAdapter
from crawlers.adapters.cafeland import CafelandAdapter
from crawlers.adapters.nhatot import NhatotAdapter
from crawlers.adapters.dothi import DothiAdapter
from crawlers.adapters.batdongsan123 import Batdongsan123Adapter

__all__ = [
    # Base classes
    "BasePlatformAdapter",
    "PlatformConfig",
    "PlatformStatus",
    "PlatformCapabilities",
    "PlatformRegistry",
    "platform_registry",
    "UnifiedListing",
    "CrawlError",
    "CrawlErrorType",
    # Platform adapters
    "BatDongSanAdapter",
    "ChototAdapter",
    "MogiAdapter",
    "AlonhadatAdapter",
    "Nhadat24hAdapter",
    "HomedyAdapter",
    "MuabanAdapter",
    "CafelandAdapter",
    "NhatotAdapter",
    "DothiAdapter",
    "Batdongsan123Adapter",
]
