"""
Mogi.vn Platform Adapter

Real estate platform with good structured data.
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


class MogiAdapter(BasePlatformAdapter):
    """Adapter for mogi.vn"""

    platform_id = "mogi"
    platform_name = "Mogi.vn"
    base_url = "https://mogi.vn"

    capabilities = PlatformCapabilities(
        supports_search=True,
        supports_detail=True,
        supports_pagination=True,
        max_results_per_page=25,
        rate_limit_requests_per_minute=12,
    )

    # City slugs for URL
    CITY_SLUGS = {
        "hanoi": "ha-noi",
        "hcm": "ho-chi-minh",
        "hochiminh": "ho-chi-minh",
        "danang": "da-nang",
        "haiphong": "hai-phong",
        "cantho": "can-tho",
        "bienhoa": "dong-nai",
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
        """Build search URL for mogi.vn"""
        # Base path for property sales
        path = "/mua-nha-dat"

        # Add city
        if city:
            city_lower = city.lower().replace(" ", "")
            city_slug = self.CITY_SLUGS.get(city_lower, city.lower().replace(" ", "-"))
            path = f"{path}/{city_slug}"

        # Build query params
        params = []

        # Price filter (in billion VND)
        if min_price:
            price_ty = min_price / 1_000_000_000
            params.append(f"cp={price_ty}")

        if max_price:
            price_ty = max_price / 1_000_000_000
            params.append(f"dp={price_ty}")

        # Area filter
        if min_area:
            params.append(f"ca={int(min_area)}")

        if max_area:
            params.append(f"da={int(max_area)}")

        # Pagination
        if page > 1:
            params.append(f"page={page}")

        # Keyword search
        if query:
            params.append(f"kw={query}")

        url = f"{self.base_url}{path}"
        if params:
            url += "?" + "&".join(params)

        return url

    def parse_search_results(self, html: str) -> list[UnifiedListing]:
        """Parse search results page"""
        soup = BeautifulSoup(html, "html.parser")
        listings: list[UnifiedListing] = []

        # Mogi listing cards
        cards = soup.select(".property-item, .props-item, article.item")

        for card in cards:
            try:
                listing = self._parse_listing_card(card)
                if listing:
                    listings.append(listing)
            except Exception as e:
                self.logger.warning(f"Failed to parse Mogi card: {e}")
                continue

        return listings

    def _parse_listing_card(self, card: Tag) -> Optional[UnifiedListing]:
        """Parse a single listing card"""
        # Title and URL
        title_link = card.select_one("a.prop-title, .title a, h2 a")
        if not title_link:
            return None

        title = title_link.get_text(strip=True)
        url = title_link.get("href", "")
        if url and not url.startswith("http"):
            url = f"{self.base_url}{url}"

        # Extract ID from URL
        listing_id = ""
        match = re.search(r"-id(\d+)$|/(\d+)\.html?$", url)
        if match:
            listing_id = match.group(1) or match.group(2)

        # Price
        price_elem = card.select_one(".price, .prop-price, .info-price")
        price_text = price_elem.get_text(strip=True) if price_elem else ""
        price = parse_vietnamese_price(price_text)

        # Area
        area_elem = card.select_one(".area, .prop-area, .info-area")
        area_text = area_elem.get_text(strip=True) if area_elem else ""
        area = parse_area(area_text)

        # Also check for area in detail attributes
        if not area:
            for attr in card.select(".attr, .info-attr span"):
                text = attr.get_text(strip=True)
                if "m²" in text or "m2" in text:
                    area = parse_area(text)
                    area_text = text
                    break

        # Location
        location_elem = card.select_one(".address, .prop-addr, .info-addr")
        location_text = location_elem.get_text(strip=True) if location_elem else ""
        city = detect_city(location_text) or detect_city(title)
        district = detect_district(location_text, city) or detect_district(title, city)

        # Image
        img = card.select_one("img.lazy, img[data-src], img")
        image_url = None
        if img:
            image_url = img.get("data-src") or img.get("data-original") or img.get("src")

        # Bedrooms/Bathrooms from attributes
        bedrooms = None
        bathrooms = None
        for attr in card.select(".attr span, .info-attr span"):
            text = attr.get_text(strip=True).lower()
            if "pn" in text or "phòng ngủ" in text:
                match = re.search(r"(\d+)", text)
                if match:
                    bedrooms = int(match.group(1))
            elif "wc" in text or "toilet" in text:
                match = re.search(r"(\d+)", text)
                if match:
                    bathrooms = int(match.group(1))

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
            bedrooms=bedrooms,
            bathrooms=bathrooms,
        )

    def parse_detail_page(self, html: str, listing_id: str) -> UnifiedListing:
        """Parse detailed listing page"""
        soup = BeautifulSoup(html, "html.parser")

        # Title
        title_elem = soup.select_one("h1.title, h1")
        title = title_elem.get_text(strip=True) if title_elem else ""

        # Price
        price_elem = soup.select_one(".price, .info-price")
        price_text = price_elem.get_text(strip=True) if price_elem else ""
        price = parse_vietnamese_price(price_text)

        # Area
        area = None
        area_text = ""

        # Description
        desc_elem = soup.select_one(".description, .content-detail, .detail-content")
        description = desc_elem.get_text(separator="\n", strip=True) if desc_elem else ""

        # Location
        addr_elem = soup.select_one(".address, .info-address")
        address = addr_elem.get_text(strip=True) if addr_elem else ""
        city = detect_city(address) or detect_city(title)
        district = detect_district(address, city) or detect_district(title, city)

        # Contact
        contact_elem = soup.select_one(".contact-name, .agent-name")
        contact_name = contact_elem.get_text(strip=True) if contact_elem else None

        phone_elem = soup.select_one(".contact-phone, .phone a, [href^='tel:']")
        phone_text = phone_elem.get_text(strip=True) if phone_elem else ""
        phones = parse_phone_numbers(phone_text + " " + description)

        # Property specs
        bedrooms = None
        bathrooms = None
        floors = None

        for row in soup.select(".info-attrs .row, .prop-info tr, .detail-info li"):
            text = row.get_text(strip=True).lower()

            if "diện tích" in text or "area" in text:
                area = parse_area(text)
                area_text = text
            elif "phòng ngủ" in text or "bedroom" in text:
                match = re.search(r"(\d+)", text)
                if match:
                    bedrooms = int(match.group(1))
            elif "toilet" in text or "wc" in text or "phòng tắm" in text:
                match = re.search(r"(\d+)", text)
                if match:
                    bathrooms = int(match.group(1))
            elif "số tầng" in text or "tầng" in text:
                match = re.search(r"(\d+)", text)
                if match:
                    floors = int(match.group(1))

        # Images
        images = []
        for img in soup.select(".gallery img, .slider img, .images img"):
            src = img.get("data-src") or img.get("src")
            if src:
                images.append(src)

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
            address=address,
            description=description,
            url=f"{self.base_url}/mua-nha-dat-id{listing_id}",
            image_url=images[0] if images else None,
            contact_name=contact_name,
            contact_phone=phones[0] if phones else None,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            floors=floors,
            raw_data={"all_images": images, "all_phones": phones},
        )

    def get_detail_url(self, listing_id: str) -> str:
        """Get URL for a specific listing"""
        return f"{self.base_url}/mua-nha-dat-id{listing_id}"


# Register the adapter
PlatformRegistry.register(MogiAdapter)
