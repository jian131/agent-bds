"""
Muaban.net Platform Adapter

Popular Vietnamese classifieds with real estate section.
"""

import re
from typing import Optional
from bs4 import BeautifulSoup, Tag

from crawlers.adapters.base import (
    BasePlatformAdapter,
    UnifiedListing,
    PlatformCapabilities,
    PlatformRegistry,
)
from parsers import (
    parse_vietnamese_price,
    parse_area,
    detect_city,
    detect_district,
    parse_phone_numbers,
)
from core.logging import CrawlLogger


class MuabanAdapter(BasePlatformAdapter):
    """Adapter for muaban.net"""

    platform_id = "muaban"
    platform_name = "Muaban.net"
    base_url = "https://muaban.net"

    capabilities = PlatformCapabilities(
        supports_search=True,
        supports_detail=True,
        supports_pagination=True,
        max_results_per_page=20,
        rate_limit_requests_per_minute=10,
    )

    CITY_SLUGS = {
        "hanoi": "ha-noi-t5",
        "hcm": "ho-chi-minh-t1",
        "hochiminh": "ho-chi-minh-t1",
        "danang": "da-nang-t17",
    }

    def __init__(self) -> None:
        super().__init__()
        self.logger = CrawlLogger(platform=self.platform_id)

    def build_search_url(
        self,
        query: str,
        city: Optional[str] = None,
        **kwargs
    ) -> str:
        """Build search URL"""
        # muaban.net uses category-based URLs
        path = "/ban-bat-dong-san"

        if city:
            city_lower = city.lower().replace(" ", "")
            city_slug = self.CITY_SLUGS.get(city_lower)
            if city_slug:
                path = f"{path}/{city_slug}"

        return f"{self.base_url}{path}"

    def parse_search_results(self, html: str) -> list[UnifiedListing]:
        """Parse search results"""
        soup = BeautifulSoup(html, "html.parser")
        listings: list[UnifiedListing] = []

        cards = soup.select(".list-item, .product-item, article")

        for card in cards:
            try:
                listing = self._parse_card(card)
                if listing:
                    listings.append(listing)
            except Exception as e:
                self.logger.warning(f"Parse error: {e}")
                continue

        return listings

    def _parse_card(self, card: Tag) -> Optional[UnifiedListing]:
        """Parse card"""
        link = card.select_one("a[href*='/ban-']")
        if not link:
            return None

        title = link.get("title", "") or link.get_text(strip=True)
        url = link.get("href", "")
        if url and not url.startswith("http"):
            url = f"{self.base_url}{url}"

        listing_id = str(hash(url))

        price_elem = card.select_one(".price, .item-price")
        price_text = price_elem.get_text(strip=True) if price_elem else ""
        price = parse_vietnamese_price(price_text)

        location_elem = card.select_one(".location, .address")
        location_text = location_elem.get_text(strip=True) if location_elem else ""
        city = detect_city(location_text) or detect_city(title)
        district = detect_district(location_text, city)

        img = card.select_one("img")
        image_url = img.get("data-src") or img.get("src") if img else None

        return UnifiedListing(
            id=f"{self.platform_id}_{listing_id}",
            platform=self.platform_id,
            title=title,
            price=price,
            price_text=price_text,
            city=city,
            district=district,
            address=location_text,
            url=url,
            image_url=image_url,
        )

    def parse_detail_page(self, html: str, listing_id: str) -> UnifiedListing:
        """Parse detail"""
        soup = BeautifulSoup(html, "html.parser")

        title_elem = soup.select_one("h1")
        title = title_elem.get_text(strip=True) if title_elem else ""

        price_elem = soup.select_one(".price")
        price_text = price_elem.get_text(strip=True) if price_elem else ""
        price = parse_vietnamese_price(price_text)

        desc_elem = soup.select_one(".description, .content")
        description = desc_elem.get_text(separator="\n", strip=True) if desc_elem else ""

        phones = parse_phone_numbers(description)

        return UnifiedListing(
            id=f"{self.platform_id}_{listing_id}",
            platform=self.platform_id,
            title=title,
            price=price,
            price_text=price_text,
            description=description,
            url=f"{self.base_url}/{listing_id}",
            contact_phone=phones[0] if phones else None,
        )

    def get_detail_url(self, listing_id: str) -> str:
        return f"{self.base_url}/{listing_id}"


PlatformRegistry.register(MuabanAdapter)
