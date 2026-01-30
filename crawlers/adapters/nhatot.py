"""
Nhatot.com Platform Adapter

Popular classifieds platform with property listings.
Similar to Chotot but separate brand.
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


class NhatotAdapter(BasePlatformAdapter):
    """Adapter for nhatot.com"""

    platform_id = "nhatot"
    platform_name = "Nhatot.com"
    base_url = "https://www.nhatot.com"

    capabilities = PlatformCapabilities(
        supports_search=True,
        supports_detail=True,
        supports_pagination=True,
        supports_api=True,
        max_results_per_page=20,
        rate_limit_requests_per_minute=12,
    )

    REGION_CODES = {
        "hanoi": 12000,
        "hcm": 13000,
        "hochiminh": 13000,
        "danang": 43000,
    }

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
        # API endpoint
        base = "https://gateway.chotot.com/v1/public/ad-listing"

        params = [
            "cg=1000",  # Real estate category
            "limit=20",
            "st=s,k",
        ]

        if city:
            city_lower = city.lower().replace(" ", "")
            region = self.REGION_CODES.get(city_lower)
            if region:
                params.append(f"region_v2={region}")

        if page > 1:
            params.append(f"o={(page - 1) * 20}")

        if query:
            params.append(f"key={query}")

        return f"{base}?{'&'.join(params)}"

    def parse_api_response(self, data: dict) -> list[UnifiedListing]:
        """Parse API response"""
        listings: list[UnifiedListing] = []

        for ad in data.get("ads", []):
            try:
                listing = self._parse_api_ad(ad)
                if listing:
                    listings.append(listing)
            except Exception as e:
                self.logger.warning(f"Parse error: {e}")
                continue

        return listings

    def _parse_api_ad(self, ad: dict) -> Optional[UnifiedListing]:
        """Parse API ad"""
        list_id = str(ad.get("list_id", ""))
        if not list_id:
            return None

        return UnifiedListing(
            id=f"{self.platform_id}_{list_id}",
            platform=self.platform_id,
            title=ad.get("subject", ""),
            price=float(ad.get("price", 0)) if ad.get("price") else None,
            price_text=ad.get("price_string", ""),
            area=float(ad.get("size", 0)) if ad.get("size") else None,
            city=detect_city(ad.get("region_name", "")),
            district=ad.get("area_name"),
            url=f"{self.base_url}/mua-ban-nha-dat/{list_id}.htm",
            bedrooms=ad.get("rooms"),
            bathrooms=ad.get("toilets"),
            raw_data=ad,
        )

    def parse_search_results(self, html: str) -> list[UnifiedListing]:
        """Parse HTML search results"""
        soup = BeautifulSoup(html, "html.parser")
        listings: list[UnifiedListing] = []

        cards = soup.select(".AdItem_wrapper__, article")

        for card in cards:
            try:
                link = card.select_one("a[href*='.htm']")
                if not link:
                    continue

                url = link.get("href", "")
                if url and not url.startswith("http"):
                    url = f"{self.base_url}{url}"

                title = link.get_text(strip=True)

                listing_id = ""
                match = re.search(r"/(\d+)\.htm", url)
                if match:
                    listing_id = match.group(1)

                price_elem = card.select_one(".AdItem_price__")
                price_text = price_elem.get_text(strip=True) if price_elem else ""

                listings.append(UnifiedListing(
                    id=f"{self.platform_id}_{listing_id}" if listing_id else f"{self.platform_id}_{hash(url)}",
                    platform=self.platform_id,
                    title=title,
                    price=parse_vietnamese_price(price_text),
                    price_text=price_text,
                    url=url,
                ))
            except Exception as e:
                self.logger.warning(f"Parse error: {e}")
                continue

        return listings

    def parse_detail_page(self, html: str, listing_id: str) -> UnifiedListing:
        """Parse detail page"""
        soup = BeautifulSoup(html, "html.parser")

        title_elem = soup.select_one("h1")
        title = title_elem.get_text(strip=True) if title_elem else ""

        price_elem = soup.select_one(".AdDecriptionVeh_price__")
        price_text = price_elem.get_text(strip=True) if price_elem else ""

        desc_elem = soup.select_one(".AdDecriptionVeh_content__")
        description = desc_elem.get_text(separator="\n", strip=True) if desc_elem else ""

        phones = parse_phone_numbers(description)

        return UnifiedListing(
            id=f"{self.platform_id}_{listing_id}",
            platform=self.platform_id,
            title=title,
            price=parse_vietnamese_price(price_text),
            price_text=price_text,
            description=description,
            url=f"{self.base_url}/mua-ban-nha-dat/{listing_id}.htm",
            contact_phone=phones[0] if phones else None,
        )

    def get_detail_url(self, listing_id: str) -> str:
        return f"{self.base_url}/mua-ban-nha-dat/{listing_id}.htm"


PlatformRegistry.register(NhatotAdapter)
