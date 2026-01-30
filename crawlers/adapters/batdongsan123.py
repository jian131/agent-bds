"""
Batdongsan123.vn Platform Adapter

Real estate classifieds platform.
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


class Batdongsan123Adapter(BasePlatformAdapter):
    """Adapter for batdongsan123.vn"""

    platform_id = "batdongsan123"
    platform_name = "Batdongsan123.vn"
    base_url = "https://batdongsan123.vn"

    capabilities = PlatformCapabilities(
        supports_search=True,
        supports_detail=True,
        supports_pagination=True,
        max_results_per_page=20,
        rate_limit_requests_per_minute=10,
    )

    def __init__(self) -> None:
        super().__init__()
        self.logger = CrawlLogger(platform=self.platform_id)

    def build_search_url(
        self,
        query: str,
        city: Optional[str] = None,
        page: int = 1,
        **kwargs
    ) -> str:
        """Build search URL"""
        path = "/ban-nha-dat"

        city_map = {
            "hanoi": "ha-noi",
            "hcm": "ho-chi-minh",
            "hochiminh": "ho-chi-minh",
        }

        if city:
            city_lower = city.lower().replace(" ", "")
            city_slug = city_map.get(city_lower, city.lower().replace(" ", "-"))
            path = f"{path}/{city_slug}"

        if page > 1:
            path = f"{path}/page/{page}"

        return f"{self.base_url}{path}"

    def parse_search_results(self, html: str) -> list[UnifiedListing]:
        """Parse search results"""
        soup = BeautifulSoup(html, "html.parser")
        listings: list[UnifiedListing] = []

        cards = soup.select(".item, .listing-item, article")

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

        title = link.get_text(strip=True)
        url = link.get("href", "")
        if url and not url.startswith("http"):
            url = f"{self.base_url}{url}"

        listing_id = str(hash(url))

        price_elem = card.select_one(".price")
        price_text = price_elem.get_text(strip=True) if price_elem else ""
        price = parse_vietnamese_price(price_text)

        area_elem = card.select_one(".area")
        area_text = area_elem.get_text(strip=True) if area_elem else ""
        area = parse_area(area_text)

        location_elem = card.select_one(".address, .location")
        location_text = location_elem.get_text(strip=True) if location_elem else ""
        city = detect_city(location_text) or detect_city(title)
        district = detect_district(location_text, city)

        img = card.select_one("img")
        image_url = img.get("src") if img else None

        return UnifiedListing(
            id=f"{self.platform_id}_{listing_id}",
            platform=self.platform_id,
            title=title,
            price=price,
            price_text=price_text,
            area=area,
            area_text=area_text,
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

        desc_elem = soup.select_one(".description")
        description = desc_elem.get_text(separator="\n", strip=True) if desc_elem else ""

        phones = parse_phone_numbers(description)

        return UnifiedListing(
            id=f"{self.platform_id}_{listing_id}",
            platform=self.platform_id,
            title=title,
            price=parse_vietnamese_price(price_text),
            price_text=price_text,
            description=description,
            url=f"{self.base_url}/{listing_id}",
            contact_phone=phones[0] if phones else None,
        )

    def get_detail_url(self, listing_id: str) -> str:
        return f"{self.base_url}/{listing_id}"


PlatformRegistry.register(Batdongsan123Adapter)
