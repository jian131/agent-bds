"""
HTTP Crawler using httpx + BeautifulSoup
Fallback for Python 3.13 + Playwright incompatibility on Windows
"""

import asyncio
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from crawlers.css_selectors import get_selectors, detect_platform
import random
import time

# User agents for rotation - more realistic
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
]


class HttpxCrawler:
    """Fast HTTP crawler without Playwright - works with Python 3.13"""

    def __init__(self):
        self.timeout = httpx.Timeout(30.0, connect=10.0)

    def _get_headers(self, url: str) -> Dict:
        """Get realistic headers for a specific domain"""
        from urllib.parse import urlparse
        domain = urlparse(url).netloc

        return {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Referer': f'https://{domain}/',
            'DNT': '1',
        }

    async def crawl_url(self, url: str) -> Optional[str]:
        """Fetch HTML from URL with retry logic"""
        max_retries = 2

        for attempt in range(max_retries):
            try:
                # Add random delay between requests
                if attempt > 0:
                    await asyncio.sleep(random.uniform(1, 3))

                async with httpx.AsyncClient(
                    timeout=self.timeout,
                    follow_redirects=True,
                    verify=False,  # Skip SSL verification for some sites
                ) as client:
                    response = await client.get(url, headers=self._get_headers(url))

                    if response.status_code == 403:
                        print(f"  ⚠️ 403 Forbidden for {url[:50]}... - site blocks bots")
                        return None

                    response.raise_for_status()
                    return response.text

            except httpx.HTTPStatusError as e:
                if attempt < max_retries - 1:
                    continue
                print(f"  ❌ HTTP {e.response.status_code} for {url[:50]}...")
                return None
            except Exception as e:
                if attempt < max_retries - 1:
                    continue
                print(f"  ❌ Error for {url[:50]}...: {type(e).__name__}")
                return None

        return None

    async def crawl_listing_page(self, url: str) -> List[Dict]:
        """
        Crawl listing page and extract data

        Returns:
            List of listings
        """
        platform = detect_platform(url)
        print(f"🌐 [HTTP] Crawling {platform}: {url[:60]}...")

        html = await self.crawl_url(url)
        if not html:
            return []

        # Determine page type
        is_list_page = self._is_list_page(url)
        page_type = 'list_page' if is_list_page else 'detail_page'

        # Get CSS selectors
        selectors = get_selectors(url, page_type)
        if not selectors:
            print(f"  ⚠️ No selectors for {platform}")
            return []

        soup = BeautifulSoup(html, 'html.parser')

        if is_list_page:
            return self._parse_list_page(soup, selectors, platform, url)
        else:
            result = self._parse_detail_page(soup, selectors, platform, url)
            return [result] if result.get('title') else []

    def _is_list_page(self, url: str) -> bool:
        """Detect if URL is list or detail page"""
        detail_patterns = [
            '/chi-tiet/', '/detail/', '/property/', '/pr',
            '/d/', '-pr', '.html', '/p/', '/listing/'
        ]
        # Check if URL has ID-like patterns
        import re
        if re.search(r'/\d+\.htm|/pr\d+|/p\d+|-\d+\.html', url):
            return False
        for pattern in detail_patterns:
            if pattern in url.lower():
                return False
        return True

    def _parse_list_page(
        self,
        soup: BeautifulSoup,
        selectors: Dict,
        platform: str,
        base_url: str
    ) -> List[Dict]:
        """Parse list page"""
        listings = []
        items_selector = selectors.get('items')
        schema = selectors.get('schema', {})

        if not items_selector:
            return []

        items = soup.select(items_selector)

        for item in items[:20]:  # Max 20 per page
            try:
                listing = self._extract_item(item, schema)

                # Add metadata
                listing['source_platform'] = platform
                listing['source_url'] = self._normalize_url(listing.get('url'), base_url)

                # Copy price to price_text for filtering
                if listing.get('price'):
                    listing['price_text'] = listing['price']

                # Validate - need at least title
                if listing.get('title'):
                    listings.append(listing)

            except Exception as e:
                continue

        print(f"  ✅ [HTTP] Extracted {len(listings)} listings")
        return listings

    def _parse_detail_page(
        self,
        soup: BeautifulSoup,
        selectors: Dict,
        platform: str,
        url: str
    ) -> Dict:
        """Parse detail page"""
        schema = selectors.get('schema', {})
        listing = self._extract_item(soup, schema)
        listing['source_platform'] = platform
        listing['source_url'] = url
        return listing

    def _extract_item(self, element, schema: Dict) -> Dict:
        """Extract data using CSS selectors"""
        listing = {}

        for field, selector in schema.items():
            try:
                if '::text' in selector:
                    sel = selector.replace('::text', '')
                    elem = element.select_one(sel)
                    listing[field] = elem.get_text(strip=True) if elem else None

                elif '::attr(' in selector:
                    attr = selector.split('::attr(')[1].rstrip(')')
                    sel = selector.split('::attr(')[0]

                    if field == 'images':  # Multiple images
                        elems = element.select(sel) if sel else []
                        listing[field] = [e.get(attr) for e in elems if e.get(attr)]
                    else:
                        elem = element.select_one(sel) if sel else element
                        listing[field] = elem.get(attr) if elem else None
                else:
                    elem = element.select_one(selector)
                    listing[field] = elem.get_text(strip=True) if elem else None

            except Exception:
                listing[field] = None

        return listing

    def _normalize_url(self, url: str, base_url: str) -> str:
        """Normalize relative URLs"""
        if not url:
            return base_url
        if url.startswith('http'):
            return url
        if url.startswith('//'):
            return 'https:' + url
        if url.startswith('/'):
            from urllib.parse import urlparse
            parsed = urlparse(base_url)
            return f"{parsed.scheme}://{parsed.netloc}{url}"
        return base_url + url

    async def crawl_multiple(
        self,
        urls: List[str],
        max_concurrent: int = 5
    ) -> List[Dict]:
        """Crawl multiple URLs"""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def crawl_with_semaphore(url: str):
            async with semaphore:
                await asyncio.sleep(random.uniform(0.5, 1.5))  # Random delay
                return await self.crawl_listing_page(url)

        tasks = [crawl_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_listings = []
        for result in results:
            if isinstance(result, list):
                all_listings.extend(result)

        return all_listings
