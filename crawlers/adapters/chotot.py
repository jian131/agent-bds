"""
Chotot.com Platform Adapter

Popular C2C marketplace with real estate listings.
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


class ChototAdapter(BasePlatformAdapter):
    """Adapter for chotot.com real estate listings"""

    platform_id = "chotot"
    platform_name = "Chợ Tốt"
    base_url = "https://nha.chotot.com"

    capabilities = PlatformCapabilities(
        supports_search=True,
        supports_detail=True,
        supports_pagination=True,
        supports_api=True,  # Chotot has a JSON API
        max_results_per_page=20,
        rate_limit_requests_per_minute=15,
    )

    # Chotot region codes
    REGION_CODES = {
        "hanoi": 12000,
        "hcm": 13000,
        "hochiminh": 13000,
        "danang": 43000,
        "haiphong": 31000,
        "cantho": 92000,
        "bienhoa": 75000,
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
        """Build search URL for chotot.com"""
        # Use the API endpoint for better structured data
        base = "https://gateway.chotot.com/v1/public/ad-listing"

        params = [
            "cg=1000",  # Category: Real estate
            "limit=20",
            "st=s,k",   # Status: selling
        ]

        # Region
        if city:
            city_lower = city.lower().replace(" ", "")
            region_code = self.REGION_CODES.get(city_lower)
            if region_code:
                params.append(f"region_v2={region_code}")

        # Price range (in VND)
        if min_price:
            params.append(f"price_min={int(min_price)}")
        if max_price:
            params.append(f"price_max={int(max_price)}")

        # Area range
        if min_area:
            params.append(f"area_min={int(min_area)}")
        if max_area:
            params.append(f"area_max={int(max_area)}")

        # Pagination
        if page > 1:
            offset = (page - 1) * 20
            params.append(f"o={offset}")

        # Search query
        if query:
            params.append(f"key={query}")

        return f"{base}?{'&'.join(params)}"

    def get_html_search_url(
        self,
        query: str,
        city: Optional[str] = None,
        page: int = 1,
        **kwargs
    ) -> str:
        """Get HTML search page URL (fallback)"""
        path = "/mua-ban-bat-dong-san"

        city_slugs = {
            "hanoi": "ha_noi",
            "hcm": "tp_ho_chi_minh",
            "hochiminh": "tp_ho_chi_minh",
            "danang": "da_nang",
        }

        params = []
        if city:
            city_lower = city.lower().replace(" ", "")
            city_slug = city_slugs.get(city_lower, "")
            if city_slug:
                params.append(f"region_name={city_slug}")

        if query:
            params.append(f"key={query}")

        if page > 1:
            params.append(f"page={page}")

        url = f"{self.base_url}{path}"
        if params:
            url += "?" + "&".join(params)
        return url

    def parse_api_response(self, data: dict) -> list[UnifiedListing]:
        """Parse JSON API response from chotot"""
        listings: list[UnifiedListing] = []

        ads = data.get("ads", [])
        for ad in ads:
            try:
                listing = self._parse_api_listing(ad)
                if listing:
                    listings.append(listing)
            except Exception as e:
                self.logger.warning(f"Failed to parse API listing: {e}")
                continue

        return listings

    def _parse_api_listing(self, ad: dict) -> Optional[UnifiedListing]:
        """Parse a single listing from API response"""
        list_id = str(ad.get("list_id", ""))
        if not list_id:
            return None

        # Basic info
        subject = ad.get("subject", "")
        price = ad.get("price")
        price_string = ad.get("price_string", "")

        # Area
        area = ad.get("size")
        area_text = f"{area} m²" if area else ""

        # Location
        region_name = ad.get("region_name", "")
        area_name = ad.get("area_name", "")  # District
        ward_name = ad.get("ward_name", "")

        location_parts = [p for p in [ward_name, area_name, region_name] if p]
        address = ", ".join(location_parts)

        city = detect_city(region_name)
        district = area_name or detect_district(subject, city)

        # Image
        image = ad.get("image")
        image_url = None
        if image:
            image_url = f"https://cdn.chotot.com/full/{image}"

        # Property details
        rooms = ad.get("rooms")
        toilets = ad.get("toilets")

        return UnifiedListing(
            id=f"{self.platform_id}_{list_id}",
            platform=self.platform_id,
            title=subject,
            price=float(price) if price else None,
            price_text=price_string,
            area=float(area) if area else None,
            area_text=area_text,
            city=city,
            district=district,
            address=address,
            url=f"{self.base_url}/{list_id}.htm",
            image_url=image_url,
            bedrooms=rooms,
            bathrooms=toilets,
            raw_data=ad,
        )

    def parse_search_results(self, html: str) -> list[UnifiedListing]:
        """Parse HTML search results (fallback)"""
        soup = BeautifulSoup(html, "html.parser")
        listings: list[UnifiedListing] = []

        # Chotot uses React with dynamic content, but there's also server-rendered data
        # Look for listing cards
        cards = soup.select("[data-testid='ad-item'], .AdItem_adItem__")

        for card in cards:
            try:
                listing = self._parse_html_card(card)
                if listing:
                    listings.append(listing)
            except Exception as e:
                self.logger.warning(f"Failed to parse HTML card: {e}")
                continue

        return listings

    def _parse_html_card(self, card: Tag) -> Optional[UnifiedListing]:
        """Parse a listing card from HTML"""
        # Title and URL
        link = card.select_one("a[href*='.htm']")
        if not link:
            return None

        url = link.get("href", "")
        if url and not url.startswith("http"):
            url = f"{self.base_url}{url}"

        # Extract ID
        listing_id = ""
        match = re.search(r"/(\d+)\.htm", url)
        if match:
            listing_id = match.group(1)

        title_elem = card.select_one("[data-testid='ad-title'], .AdItem_title__")
        title = title_elem.get_text(strip=True) if title_elem else link.get_text(strip=True)

        # Price
        price_elem = card.select_one("[data-testid='ad-price'], .AdItem_price__")
        price_text = price_elem.get_text(strip=True) if price_elem else ""
        price = parse_vietnamese_price(price_text)

        # Area from params
        params_elem = card.select_one("[data-testid='ad-params'], .AdItem_params__")
        params_text = params_elem.get_text(strip=True) if params_elem else ""
        area = parse_area(params_text)

        # Location
        location_elem = card.select_one("[data-testid='ad-location'], .AdItem_location__")
        location_text = location_elem.get_text(strip=True) if location_elem else ""
        city = detect_city(location_text)
        district = detect_district(location_text, city)

        # Image
        img = card.select_one("img")
        image_url = img.get("src") if img else None

        return UnifiedListing(
            id=f"{self.platform_id}_{listing_id}" if listing_id else f"{self.platform_id}_{hash(url)}",
            platform=self.platform_id,
            title=title,
            price=price,
            price_text=price_text,
            area=area,
            area_text=params_text,
            city=city,
            district=district,
            address=location_text,
            url=url,
            image_url=image_url,
        )

    def parse_detail_page(self, html: str, listing_id: str) -> UnifiedListing:
        """Parse detailed listing page"""
        soup = BeautifulSoup(html, "html.parser")

        # Title
        title_elem = soup.select_one("h1, [data-testid='ad-title']")
        title = title_elem.get_text(strip=True) if title_elem else ""

        # Price
        price_elem = soup.select_one("[data-testid='ad-price'], .AdDecriptionVeh_price__")
        price_text = price_elem.get_text(strip=True) if price_elem else ""
        price = parse_vietnamese_price(price_text)

        # Description
        desc_elem = soup.select_one("[data-testid='ad-description'], .AdDecriptionVeh_content__")
        description = desc_elem.get_text(separator="\n", strip=True) if desc_elem else ""

        # Contact
        phone_elem = soup.select_one("[data-testid='phone-button'], .CallButton_")
        phone_text = ""
        phones = parse_phone_numbers(description)

        # Location
        location_elem = soup.select_one("[data-testid='ad-location']")
        location_text = location_elem.get_text(strip=True) if location_elem else ""
        city = detect_city(location_text)
        district = detect_district(location_text, city)

        # Property params
        area = None
        bedrooms = None
        bathrooms = None

        for param in soup.select("[data-testid='param-item'], .AdParam_item__"):
            text = param.get_text(strip=True).lower()

            if "m²" in text or "m2" in text:
                area = parse_area(text)
            elif "phòng ngủ" in text or "pn" in text:
                match = re.search(r"(\d+)", text)
                if match:
                    bedrooms = int(match.group(1))
            elif "toilet" in text or "wc" in text:
                match = re.search(r"(\d+)", text)
                if match:
                    bathrooms = int(match.group(1))

        # Images
        images = []
        for img in soup.select("[data-testid='gallery-image'] img, .AdGallery_ img"):
            src = img.get("src") or img.get("data-src")
            if src:
                images.append(src)

        return UnifiedListing(
            id=f"{self.platform_id}_{listing_id}",
            platform=self.platform_id,
            title=title,
            price=price,
            price_text=price_text,
            area=area,
            city=city,
            district=district,
            address=location_text,
            description=description,
            url=f"{self.base_url}/{listing_id}.htm",
            image_url=images[0] if images else None,
            contact_phone=phones[0] if phones else None,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            raw_data={"all_images": images, "all_phones": phones},
        )

    def get_detail_url(self, listing_id: str) -> str:
        """Get URL for a specific listing"""
        return f"{self.base_url}/{listing_id}.htm"


# Register the adapter
PlatformRegistry.register(ChototAdapter)
