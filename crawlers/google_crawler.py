"""
Google Search Crawler - Find property listing URLs
"""

from typing import List, Dict
from crawlers.base_crawler import BaseCrawler
from crawlers.css_selectors import detect_platform
import re

class GoogleSearchCrawler(BaseCrawler):
    """Crawler for Google search results"""

    async def search_properties(self, query: str, max_results: int = 15) -> List[Dict]:
        """
        Search Google for property listings

        Args:
            query: Search query (e.g., "chung cư 2PN Cầu Giấy 2-3 tỷ")
            max_results: Maximum results to return

        Returns:
            List of {url, title, platform, priority}
        """

        print(f"\n🔍 Google Search: {query}")

        # Build Google search URL
        search_query = self._build_search_query(query)
        google_url = f"https://www.google.com/search?q={search_query}&num={max_results}"

        # Crawl Google results page
        result = await self.crawl_url(
            url=google_url,
            css_selector='#search',  # Main search results container
            wait_for='#search'
        )

        if not result:
            print("❌ Google search failed")
            return []

        # Extract URLs from markdown (cleaner than HTML)
        urls = self._extract_urls_from_markdown(result['markdown'])

        # Filter and prioritize
        filtered = self._filter_and_prioritize(urls)

        print(f"✅ Found {len(filtered)} relevant URLs from Google")

        return filtered[:max_results]

    def _build_search_query(self, user_query: str) -> str:
        """Convert user query to Google search query"""

        # Remove stopwords
        stopwords = ['tìm', 'kiếm', 'cho', 'tôi', 'muốn', 'cần', 'giúp']
        query_lower = user_query.lower()

        for word in stopwords:
            query_lower = query_lower.replace(word, '')

        # Add location if not present
        if 'hà nội' not in query_lower and 'hanoi' not in query_lower:
            query_lower += ' hà nội'

        # Add "bán" if not present
        if 'bán' not in query_lower and 'mua' not in query_lower:
            query_lower = 'bán ' + query_lower

        return query_lower.strip().replace(' ', '+')

    def _extract_urls_from_markdown(self, markdown: str) -> List[str]:
        """Extract URLs from markdown content"""

        # Regex to find markdown links [text](url)
        url_pattern = r'\[.*?\]\((https?://[^\)]+)\)'
        matches = re.findall(url_pattern, markdown)

        # Also find plain URLs
        plain_url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        plain_matches = re.findall(plain_url_pattern, markdown)

        all_urls = list(set(matches + plain_matches))

        return all_urls

    def _filter_and_prioritize(self, urls: List[str]) -> List[Dict]:
        """Filter relevant URLs and assign priority"""

        # Relevant platforms
        relevant_platforms = [
            'chotot.com',
            'batdongsan.com.vn',
            'mogi.vn',
            'alonhadat.com.vn',
            'nhadat247.com.vn',
            'muaban.net',
            'facebook.com/groups'
        ]

        # Exclude patterns
        exclude_patterns = [
            'google.com',
            'youtube.com',
            'vnexpress.net',
            'dantri.com.vn',
            'thanhnien.vn',
            'tuoitre.vn',
            '/tag/',
            '/category/',
            '/tin-tuc/',
            '/blog/'
        ]

        filtered = []

        for url in urls:
            url_lower = url.lower()

            # Check if relevant
            is_relevant = any(platform in url_lower for platform in relevant_platforms)

            # Check if excluded
            is_excluded = any(pattern in url_lower for pattern in exclude_patterns)

            if is_relevant and not is_excluded:
                platform = detect_platform(url)
                priority = self._calculate_priority(url)

                filtered.append({
                    'url': url,
                    'platform': platform,
                    'priority': priority
                })

        # Sort by priority
        filtered.sort(key=lambda x: x['priority'])

        return filtered

    def _calculate_priority(self, url: str) -> int:
        """Calculate priority (1=highest, 3=lowest)"""

        url_lower = url.lower()

        # Priority 1: Direct listing pages
        listing_indicators = ['/chi-tiet', '/listing/', '-i.', '.html', '/p-']
        if any(ind in url_lower for ind in listing_indicators):
            return 1

        # Priority 2: List/search pages
        list_indicators = ['/nha-dat-ban', '/mua-ban', '/search', '/tim-kiem']
        if any(ind in url_lower for ind in list_indicators):
            return 2

        # Priority 3: Groups, forums
        return 3
