"""
BatDongSan.com.vn Platform Adapter

Vietnam's largest real estate platform.
"""

import re
from typing import Optional
from bs4 import BeautifulSoup, Tag

from crawlers.adapters.base import (
    BasePlatformAdapter,
    UnifiedListing,
    PlatformCapabilities,
    PlatformRegistry,
    CrawlError,
    RateLimitError,
    BlockedError,
)
from parsers import (
    parse_vietnamese_price,
    parse_area,
    detect_city,
    detect_district,
    parse_phone_numbers,
)
from core.logging import CrawlLogger


class BatDongSanAdapter(BasePlatformAdapter):
    """Adapter for batdongsan.com.vn"""

    platform_id = "batdongsan"
    platform_name = "BatDongSan.com.vn"
    base_url = "https://batdongsan.com.vn"

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
        district: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_area: Optional[float] = None,
        max_area: Optional[float] = None,
        page: int = 1,
        **kwargs
    ) -> str:
        """Build search URL for batdongsan.com.vn"""
        # Base search path
        path = "/nha-dat-ban"

        # City mapping
        city_slugs = {
            "hanoi": "ha-noi",
            "hcm": "tp-hcm",
            "hochiminh": "tp-hcm",
            "danang": "da-nang",
            "haiphong": "hai-phong",
        }

        if city:
            city_lower = city.lower().replace(" ", "")
            city_slug = city_slugs.get(city_lower, city.lower().replace(" ", "-"))
            path = f"{path}/{city_slug}"

        # Build query params
        params = []

        if min_price:
            # Convert to billion VND
            price_ty = min_price / 1_000_000_000
            params.append(f"giaFrom={price_ty}")

        if max_price:
            price_ty = max_price / 1_000_000_000
            params.append(f"giaTo={price_ty}")

        if min_area:
            params.append(f"dienTichFrom={min_area}")

        if max_area:
            params.append(f"dienTichTo={max_area}")

        if page > 1:
            params.append(f"page={page}")

        if query:
            params.append(f"keyword={query}")

        url = f"{self.base_url}{path}"
        if params:
            url += "?" + "&".join(params)

        return url

    def parse_search_results(self, html: str) -> list[UnifiedListing]:
        """Parse search results page"""
        soup = BeautifulSoup(html, "html.parser")
        listings: list[UnifiedListing] = []

        # Find listing items - batdongsan uses various container classes
        containers = soup.select(".js__card, .re__card-full, .product-item")

        for container in containers:
            try:
                listing = self._parse_listing_card(container)
                if listing:
                    listings.append(listing)
            except Exception as e:
                self.logger.warning(f"Failed to parse listing card: {e}")
                continue

        return listings

    def _parse_listing_card(self, card: Tag) -> Optional[UnifiedListing]:
        """Parse a single listing card"""
        # Title and URL
        title_elem = card.select_one(".re__card-title, .title a, h3 a")
        if not title_elem:
            return None

        title = title_elem.get_text(strip=True)
        url = title_elem.get("href", "")
        if url and not url.startswith("http"):
            url = f"{self.base_url}{url}"

        # Extract listing ID from URL
        listing_id = ""
        if url:
            match = re.search(r"-pr(\d+)\.html?$|/(\d+)$", url)
            if match:
                listing_id = match.group(1) or match.group(2)

        # Price
        price_elem = card.select_one(".re__card-price, .price, .product-price")
        price_text = price_elem.get_text(strip=True) if price_elem else ""
        price = parse_vietnamese_price(price_text)

        # Area
        area_elem = card.select_one(".re__card-area, .area, .product-area")
        area_text = area_elem.get_text(strip=True) if area_elem else ""
        area = parse_area(area_text)

        # Location
        location_elem = card.select_one(".re__card-location, .location, .product-location")
        location_text = location_elem.get_text(strip=True) if location_elem else ""
        city = detect_city(location_text) or detect_city(title)
        district = detect_district(location_text, city) or detect_district(title, city)

        # Image
        img_elem = card.select_one("img[src], img[data-src]")
        image_url = None
        if img_elem:
            image_url = img_elem.get("data-src") or img_elem.get("src")

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
            raw_data={"html_snippet": str(card)[:500]},
        )

    def parse_detail_page(self, html: str, listing_id: str) -> UnifiedListing:
        """Parse detailed listing page"""
        soup = BeautifulSoup(html, "html.parser")

        # Title
        title_elem = soup.select_one("h1, .re__pr-title")
        title = title_elem.get_text(strip=True) if title_elem else ""

        # Price
        price_elem = soup.select_one(".re__pr-short-price, .price, .js__pr-price")
        price_text = price_elem.get_text(strip=True) if price_elem else ""
        price = parse_vietnamese_price(price_text)

        # Area
        area_elem = soup.select_one(".re__pr-short-area, .js__pr-area")
        area_text = area_elem.get_text(strip=True) if area_elem else ""
        area = parse_area(area_text)

        # Description
        desc_elem = soup.select_one(".re__pr-description, .description")
        description = desc_elem.get_text(separator="\n", strip=True) if desc_elem else ""

        # Location
        location_elem = soup.select_one(".re__pr-short-location, .js__pr-location")
        location_text = location_elem.get_text(strip=True) if location_elem else ""
        city = detect_city(location_text) or detect_city(title)
        district = detect_district(location_text, city) or detect_district(title, city)

        # Contact info
        contact_elem = soup.select_one(".re__contact-name, .contact-name")
        contact_name = contact_elem.get_text(strip=True) if contact_elem else None

        phone_elem = soup.select_one(".re__btn-phone, .phone-number, [href^='tel:']")
        phone_text = phone_elem.get_text(strip=True) if phone_elem else ""
        phones = parse_phone_numbers(phone_text + " " + description)

        # Images
        images = []
        for img in soup.select(".re__pr-gallery img, .swiper-slide img"):
            src = img.get("data-src") or img.get("src")
            if src:
                images.append(src)

        # Property details
        bedrooms = None
        bathrooms = None
        floors = None

        for detail in soup.select(".re__pr-specs-content-item, .re__pr-detail-value"):
            text = detail.get_text(strip=True).lower()
            label_elem = detail.find_previous_sibling()
            label = label_elem.get_text(strip=True).lower() if label_elem else ""

            if "phòng ngủ" in label or "bedroom" in label:
                match = re.search(r"(\d+)", text)
                if match:
                    bedrooms = int(match.group(1))
            elif "phòng tắm" in label or "toilet" in label or "wc" in label:
                match = re.search(r"(\d+)", text)
                if match:
                    bathrooms = int(match.group(1))
            elif "số tầng" in label or "tầng" in label:
                match = re.search(r"(\d+)", text)
                if match:
                    floors = int(match.group(1))

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
            description=description,
            url=f"{self.base_url}/ban-nha-pr{listing_id}",
            image_url=images[0] if images else None,
            contact_name=contact_name,
            contact_phone=phones[0] if phones else None,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            floors=floors,
            raw_data={
                "all_images": images,
                "all_phones": phones,
            },
        )

    def get_detail_url(self, listing_id: str) -> str:
        """Get URL for a specific listing"""
        # batdongsan URLs have format: /ban-nha-...-pr12345.html
        return f"{self.base_url}/ban-nha-pr{listing_id}.html"


# Register the adapter
PlatformRegistry.register(BatDongSanAdapter)
