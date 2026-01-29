"""
Platform-specific crawlers với CSS selectors (FAST)
"""

from typing import List, Dict, Optional
from crawlers.base_crawler import BaseCrawler
from crawlers.css_selectors import get_selectors, detect_platform
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
import json

class PlatformCrawler(BaseCrawler):
    """Fast crawler using CSS selectors"""

    async def crawl_listing_page(self, url: str) -> List[Dict]:
        """
        Crawl single listing or list page

        Returns:
            List of listings (even if single page)
        """

        platform = detect_platform(url)
        print(f"🌐 Crawling {platform}: {url[:60]}...")

        # Determine page type
        is_list_page = self._is_list_page(url)
        page_type = 'list_page' if is_list_page else 'detail_page'

        # Get CSS selectors for platform
        selectors = get_selectors(url, page_type)

        if not selectors:
            # Fallback to LLM extraction
            return await self._crawl_with_llm(url, platform)

        # Fast CSS extraction
        return await self._crawl_with_css(url, platform, selectors, is_list_page)

    async def _crawl_with_css(
        self,
        url: str,
        platform: str,
        selectors: Dict,
        is_list_page: bool
    ) -> List[Dict]:
        """Fast CSS-based extraction"""

        # Wait for content to load
        items_selector = selectors.get('items', 'body')

        # Crawl page
        result = await self.crawl_url(
            url=url,
            css_selector=items_selector if is_list_page else None,
            wait_for=items_selector if is_list_page else None
        )

        if not result:
            return []

        # Parse HTML với CSS selectors
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(result['html'], 'html.parser')

        if is_list_page:
            return self._parse_list_page(soup, selectors, platform, url)
        else:
            return [self._parse_detail_page(soup, selectors, platform, url)]

    def _parse_list_page(
        self,
        soup,
        selectors: Dict,
        platform: str,
        base_url: str
    ) -> List[Dict]:
        """Parse list page với CSS selectors"""

        listings = []
        items_selector = selectors.get('items')
        schema = selectors.get('schema', {})

        items = soup.select(items_selector)

        for item in items[:20]:  # Max 20 per page
            try:
                listing = {}

                for field, selector in schema.items():
                    # Parse CSS selector
                    if '::text' in selector:
                        sel = selector.replace('::text', '')
                        elem = item.select_one(sel)
                        listing[field] = elem.get_text(strip=True) if elem else None

                    elif '::attr(' in selector:
                        attr_match = selector.split('::attr(')[1].rstrip(')')
                        sel = selector.split('::attr(')[0]
                        elem = item.select_one(sel) if sel else item
                        listing[field] = elem.get(attr_match) if elem else None

                    else:
                        elem = item.select_one(selector)
                        listing[field] = elem.get_text(strip=True) if elem else None

                # Add metadata
                listing['source_platform'] = platform
                listing['source_url'] = self._normalize_url(listing.get('url'), base_url)

                # Copy price to price_text for filtering
                if listing.get('price'):
                    listing['price_text'] = listing['price']

                # Validate
                if listing.get('title') and listing.get('price'):
                    listings.append(listing)

            except Exception as e:
                print(f"  ⚠️ Parse error: {e}")
                continue

        print(f"  ✅ Extracted {len(listings)} listings")
        return listings

    def _parse_detail_page(
        self,
        soup,
        selectors: Dict,
        platform: str,
        url: str
    ) -> Dict:
        """Parse detail page"""

        listing = {}
        schema = selectors.get('schema', {})

        for field, selector in schema.items():
            try:
                if '::text' in selector:
                    sel = selector.replace('::text', '')
                    elem = soup.select_one(sel)
                    listing[field] = elem.get_text(strip=True) if elem else None

                elif '::attr(' in selector:
                    attr = selector.split('::attr(')[1].rstrip(')')
                    sel = selector.split('::attr(')[0]

                    if field == 'images':  # Multiple images
                        elems = soup.select(sel)
                        listing[field] = [e.get(attr) for e in elems if e.get(attr)]
                    else:
                        elem = soup.select_one(sel)
                        listing[field] = elem.get(attr) if elem else None

                else:
                    elem = soup.select_one(selector)
                    listing[field] = elem.get_text(strip=True) if elem else None

            except Exception as e:
                print(f"  ⚠️ Field {field} error: {e}")
                listing[field] = None

        listing['source_platform'] = platform
        listing['source_url'] = url

        return listing

    async def _crawl_with_llm(self, url: str, platform: str) -> List[Dict]:
        """Fallback: LLM-based extraction for unknown platforms"""

        print(f"  ℹ️ No CSS selectors, using LLM fallback...")

        instruction = """
        Extract property listings from this page.

        For each listing extract:
        - title: Property title
        - price: Price (keep original text like "3 tỷ 500 triệu")
        - area: Area in m2
        - location: Full address
        - bedrooms: Number of bedrooms (if available)
        - bathrooms: Number of bathrooms (if available)
        - contact: Phone number (if available)
        - images: Image URLs (if available)
        - url: Listing URL (if this is a list page)

        Return JSON array of listings.
        If this is a single listing page, return array with 1 item.
        """

        extraction_strategy = self.create_llm_extraction(instruction)

        result = await self.crawl_url(
            url=url,
            extraction_strategy=extraction_strategy
        )

        if not result or not result.get('extracted_content'):
            return []

        try:
            listings = json.loads(result['extracted_content'])

            # Add metadata
            for listing in listings:
                listing['source_platform'] = platform
                if not listing.get('url'):
                    listing['source_url'] = url
                else:
                    listing['source_url'] = self._normalize_url(listing['url'], url)

            print(f"  ✅ LLM extracted {len(listings)} listings")
            return listings

        except:
            return []

    def _is_list_page(self, url: str) -> bool:
        """Detect if URL is a list page or single listing"""

        list_indicators = [
            '/nha-dat-ban',
            '/mua-ban',
            '/search',
            '/tim-kiem',
            '/danh-sach',
            '/list'
        ]

        detail_indicators = [
            '/chi-tiet',
            '/detail',
            '/listing/',
            '-i.',
            '.html'
        ]

        url_lower = url.lower()

        # Check detail first (more specific)
        if any(ind in url_lower for ind in detail_indicators):
            return False

        # Check list
        if any(ind in url_lower for ind in list_indicators):
            return True

        # Default: assume list page
        return True

    def _normalize_url(self, url: Optional[str], base_url: str) -> str:
        """Normalize relative URL to absolute"""

        if not url:
            return base_url

        if url.startswith('http'):
            return url

        # Relative URL
        from urllib.parse import urljoin
        return urljoin(base_url, url)
