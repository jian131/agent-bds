"""
Base Platform Adapter Interface.
All platform-specific crawlers must implement this interface.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any, Type
import asyncio
import time
import random

from pydantic import BaseModel, Field

from core.logging import CrawlLogger


class PlatformStatus(str, Enum):
    """Platform availability status."""
    ACTIVE = "active"
    BLOCKED = "blocked"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"
    DISABLED = "disabled"


class CrawlErrorType(str, Enum):
    """Types of crawl errors."""
    TIMEOUT = "timeout"
    BLOCKED = "blocked"
    RATE_LIMITED = "rate_limited"
    PARSE_ERROR = "parse_error"
    NETWORK_ERROR = "network_error"
    NOT_FOUND = "not_found"
    UNKNOWN = "unknown"


@dataclass
class CrawlError(Exception):
    """Structured crawl error that can also be raised as exception."""
    error_type: CrawlErrorType
    message: str
    url: str = ""
    platform: str = ""
    status_code: Optional[int] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def __str__(self) -> str:
        return f"{self.error_type.value}: {self.message}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_type": self.error_type.value,
            "message": self.message,
            "url": self.url,
            "platform": self.platform,
            "status_code": self.status_code,
            "timestamp": self.timestamp.isoformat(),
        }


# Convenience exception classes
class RateLimitError(CrawlError):
    """Raised when rate limited."""
    def __init__(self, message: str = "Rate limited", **kwargs):
        super().__init__(
            error_type=CrawlErrorType.RATE_LIMITED,
            message=message,
            **kwargs
        )


class BlockedError(CrawlError):
    """Raised when blocked (403, captcha, etc)."""
    def __init__(self, message: str = "Blocked by platform", **kwargs):
        super().__init__(
            error_type=CrawlErrorType.BLOCKED,
            message=message,
            **kwargs
        )


class UnifiedListing(BaseModel):
    """
    Unified listing schema across all platforms.

    This is a simplified schema that all adapters produce.
    Fields map to common real estate listing attributes.
    """

    # Core identifiers
    id: str = Field(..., description="Unique listing identifier (platform_id)")
    platform: str = Field(..., description="Platform identifier")

    # Title and description
    title: str = Field("", description="Listing title")
    description: Optional[str] = Field(None, description="Full description")

    # Price (normalized to VND)
    price: Optional[float] = Field(None, description="Price in VND")
    price_text: Optional[str] = Field(None, description="Original price text")

    # Area (normalized to m²)
    area: Optional[float] = Field(None, description="Area in square meters")
    area_text: Optional[str] = Field(None, description="Original area text")

    # Location
    address: Optional[str] = Field(None, description="Full address")
    ward: Optional[str] = Field(None, description="Ward/Phường")
    district: Optional[str] = Field(None, description="District/Quận")
    city: Optional[str] = Field(None, description="City/Thành phố")

    # Contact info
    contact_name: Optional[str] = Field(None, description="Contact person name")
    contact_phone: Optional[str] = Field(None, description="Primary phone number")
    contact_zalo: Optional[str] = Field(None, description="Zalo number")
    contact_email: Optional[str] = Field(None, description="Email address")

    # Property details
    property_type: Optional[str] = Field(None, description="Property type")
    bedrooms: Optional[int] = Field(None, description="Number of bedrooms")
    bathrooms: Optional[int] = Field(None, description="Number of bathrooms")
    floors: Optional[int] = Field(None, description="Number of floors")
    direction: Optional[str] = Field(None, description="House direction")

    # Media
    image_url: Optional[str] = Field(None, description="Main image URL")
    images: List[str] = Field(default_factory=list, description="All image URLs")

    # URLs
    url: str = Field("", description="Original listing URL")

    # Timestamps
    posted_at: Optional[datetime] = Field(None, description="When listing was posted")
    crawled_at: datetime = Field(default_factory=datetime.utcnow, description="When crawled")

    # Raw data for debugging (excluded from serialization)
    raw_data: Optional[Dict[str, Any]] = Field(None, exclude=True)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


@dataclass
class PlatformCapabilities:
    """Describes what a platform adapter supports."""
    supports_search: bool = True
    supports_detail: bool = True
    supports_pagination: bool = True
    supports_api: bool = False  # Has JSON API vs HTML only
    max_results_per_page: int = 20
    rate_limit_requests_per_minute: int = 10


@dataclass
class PlatformConfig:
    """Configuration for a platform adapter."""
    name: str
    base_url: str
    enabled: bool = True
    rate_limit_rpm: int = 30  # Requests per minute
    timeout_seconds: int = 30
    max_retries: int = 3
    respect_robots_txt: bool = True
    backoff_base: float = 1.0
    backoff_max: float = 60.0
    jitter_range: tuple = (0.5, 1.5)


class BasePlatformAdapter(ABC):
    """
    Abstract base class for platform-specific crawlers.

    Each adapter should define:
    - platform_id: Unique identifier
    - platform_name: Human readable name
    - base_url: Base URL for the platform
    - capabilities: What the platform supports

    And implement:
    - build_search_url(): Build search URL from params
    - parse_search_results(): Parse HTML search results
    - parse_detail_page(): Parse HTML detail page
    - get_detail_url(): Build detail page URL
    """

    # Class attributes to be set by subclasses
    platform_id: str = ""
    platform_name: str = ""
    base_url: str = ""
    capabilities: PlatformCapabilities = field(default_factory=PlatformCapabilities)

    def __init__(self):
        self.logger = CrawlLogger(self.platform_id or "unknown")
        self._status = PlatformStatus.ACTIVE
        self._blocked_until: Optional[datetime] = None
        self._request_count = 0
        self._error_count = 0

    @property
    def status(self) -> PlatformStatus:
        if self._blocked_until and datetime.utcnow() < self._blocked_until:
            return PlatformStatus.BLOCKED
        return self._status

    @property
    def is_available(self) -> bool:
        return self.status == PlatformStatus.ACTIVE

    @abstractmethod
    def build_search_url(
        self,
        query: str,
        city: Optional[str] = None,
        district: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_area: Optional[float] = None,
        max_area: Optional[float] = None,
        page: int = 1,
        **kwargs
    ) -> str:
        """Build search URL from query and filters."""
        pass

    @abstractmethod
    def parse_search_results(self, html: str) -> List[UnifiedListing]:
        """Parse search results HTML into listings."""
        pass

    @abstractmethod
    def parse_detail_page(self, html: str, listing_id: str) -> UnifiedListing:
        """Parse detail page HTML into listing."""
        pass

    @abstractmethod
    def get_detail_url(self, listing_id: str) -> str:
        """Build URL for a specific listing."""
        pass

    def get_stats(self) -> Dict[str, Any]:
        """Get platform statistics."""
        return {
            "platform_id": self.platform_id,
            "platform_name": self.platform_name,
            "status": self.status.value,
            "base_url": self.base_url,
            "request_count": self._request_count,
            "error_count": self._error_count,
            "blocked_until": self._blocked_until.isoformat() if self._blocked_until else None,
            "capabilities": {
                "supports_search": self.capabilities.supports_search,
                "supports_detail": self.capabilities.supports_detail,
                "supports_api": self.capabilities.supports_api,
                "rate_limit_rpm": self.capabilities.rate_limit_requests_per_minute,
            }
        }


class PlatformRegistry:
    """
    Registry for managing platform adapters.

    Adapters register themselves when imported:
        PlatformRegistry.register(MyAdapter)
    """

    _adapters: Dict[str, Type[BasePlatformAdapter]] = {}
    _instances: Dict[str, BasePlatformAdapter] = {}

    @classmethod
    def register(cls, adapter_class: Type[BasePlatformAdapter]) -> None:
        """Register a platform adapter class."""
        # Get instance to read platform_id
        instance = adapter_class()
        cls._adapters[instance.platform_id] = adapter_class
        cls._instances[instance.platform_id] = instance

    @classmethod
    def get(cls, platform_id: str) -> Optional[BasePlatformAdapter]:
        """Get adapter instance by platform ID."""
        return cls._instances.get(platform_id)

    @classmethod
    def get_all(cls) -> Dict[str, BasePlatformAdapter]:
        """Get all adapter instances."""
        return cls._instances.copy()

    @classmethod
    def get_available(cls) -> List[BasePlatformAdapter]:
        """Get all available (not blocked) adapters."""
        return [a for a in cls._instances.values() if a.is_available]

    @classmethod
    def list_platforms(cls) -> List[Dict[str, Any]]:
        """Get info about all registered platforms."""
        return [
            {
                "id": adapter.platform_id,
                "name": adapter.platform_name,
                "base_url": adapter.base_url,
                "status": adapter.status.value,
            }
            for adapter in cls._instances.values()
        ]

    @classmethod
    def get_stats(cls) -> List[Dict[str, Any]]:
        """Get stats for all platforms."""
        return [a.get_stats() for a in cls._instances.values()]


# Global registry instance (for backward compatibility)
platform_registry = PlatformRegistry()
