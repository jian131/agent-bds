"""
Nha.chotot.com / Alonhadat.com.vn Platform Adapter

Alonhadat is a dedicated real estate platform.
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


class AlonhadatAdapter(BasePlatformAdapter):
    """Adapter for alonhadat.com.vn"""

    platform_id = "alonhadat"
    platform_name = "Alonhadat.com.vn"
    base_url = "https://alonhadat.com.vn"

    capabilities = PlatformCapabilities(
        supports_search=True,
        supports_detail=True,
        supports_pagination=True,
        max_results_per_page=20,
        rate_limit_requests_per_minute=10,
    )

    CITY_SLUGS = {
        "hanoi": "ha-noi",
        "hcm": "tp-hcm",
        "hochiminh": "tp-hcm",
        "danang": "da-nang",
        "haiphong": "hai-phong",
    }

    def __init__(self) -> None:
        super().__init__()
        self.logger = CrawlLogger(platform=self.platform_id)

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
        """Build search URL"""
        path = "/nha-dat/can-ban"

        if city:
            city_lower = city.lower().replace(" ", "")
            city_slug = self.CITY_SLUGS.get(city_lower, city.lower().replace(" ", "-"))
            path = f"{path}/{city_slug}"

        params = []

        if min_price:
            price_ty = min_price / 1_000_000_000
            params.append(f"gia-tu-{price_ty}-ty")

        if max_price:
            price_ty = max_price / 1_000_000_000
            params.append(f"gia-den-{price_ty}-ty")

        if page > 1:
            params.append(f"trang-{page}")

        url = f"{self.base_url}{path}"
        if params:
            url += "/" + "/".join(params)

        return url

    def parse_search_results(self, html: str) -> list[UnifiedListing]:
        """Parse search results"""
        soup = BeautifulSoup(html, "html.parser")
        listings: list[UnifiedListing] = []

        cards = soup.select(".content-item, .property-item, article.item")

        for card in cards:
            try:
                listing = self._parse_card(card)
                if listing:
                    listings.append(listing)
            except Exception as e:
                self.logger.warning(f"Failed to parse alonhadat card: {e}")
                continue

        return listings

    def _parse_card(self, card: Tag) -> Optional[UnifiedListing]:
        """Parse listing card"""
        title_elem = card.select_one("a.title, h3 a, .property-title a")
        if not title_elem:
            return None

        title = title_elem.get_text(strip=True)
        url = title_elem.get("href", "")
        if url and not url.startswith("http"):
            url = f"{self.base_url}{url}"

        listing_id = ""
        match = re.search(r"/(\d+)\.html?$|-(\d+)$", url)
        if match:
            listing_id = match.group(1) or match.group(2)

        price_elem = card.select_one(".price, .property-price")
        price_text = price_elem.get_text(strip=True) if price_elem else ""
        price = parse_vietnamese_price(price_text)

        area_elem = card.select_one(".area, .property-area")
        area_text = area_elem.get_text(strip=True) if area_elem else ""
        area = parse_area(area_text)

        location_elem = card.select_one(".address, .property-location")
        location_text = location_elem.get_text(strip=True) if location_elem else ""
        city = detect_city(location_text) or detect_city(title)
        district = detect_district(location_text, city)

        img = card.select_one("img")
        image_url = img.get("data-src") or img.get("src") if img else None

        return UnifiedListing(
            id=f"{self.platform_id}_{listing_id}" if listing_id else f"{self.platform_id}_{hash(url)}",
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
        """Parse detail page"""
        soup = BeautifulSoup(html, "html.parser")

        title_elem = soup.select_one("h1")
        title = title_elem.get_text(strip=True) if title_elem else ""

        price_elem = soup.select_one(".price, .property-price")
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
            url=f"{self.base_url}/nha-dat/{listing_id}.html",
            contact_phone=phones[0] if phones else None,
        )

    def get_detail_url(self, listing_id: str) -> str:
        return f"{self.base_url}/nha-dat/{listing_id}.html"


# Register
PlatformRegistry.register(AlonhadatAdapter)
