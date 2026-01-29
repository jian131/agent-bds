"""
Facebook Groups & Marketplace Crawler
"""

from typing import List, Dict, Optional
from crawlers.base_crawler import BaseCrawler
from crawlers.css_selectors import PLATFORM_SELECTORS
from bs4 import BeautifulSoup
import re


class FacebookCrawler(BaseCrawler):
    """Specialized Facebook crawler"""

    # Known BĐS groups by location
    KNOWN_GROUPS = {
        'cầu giấy': [
            'https://www.facebook.com/groups/muabannhadatcaugiay',
            'https://www.facebook.com/groups/bdscaugiay',
        ],
        'ba đình': [
            'https://www.facebook.com/groups/muabannhadatbadinh',
        ],
        'đống đa': [
            'https://www.facebook.com/groups/bdsdongda',
        ],
        'tây hồ': [
            'https://www.facebook.com/groups/bdstayho',
        ],
        'thanh xuân': [
            'https://www.facebook.com/groups/bdsthanhxuan',
        ],
        'hà đông': [
            'https://www.facebook.com/groups/bdshadong',
        ],
        'hà nội': [
            'https://www.facebook.com/groups/muabannhadathanoi',
            'https://www.facebook.com/groups/bdshanoi247',
        ]
    }

    async def crawl_facebook_groups(self, query: str) -> List[Dict]:
        """
        Find and crawl Facebook groups

        Strategy:
        1. Find known groups for location
        2. Google search for more groups
        3. Crawl each group
        """

        print(f"\n🔵 Facebook Groups Search: {query}")

        # Get location from query
        location = self._extract_location(query)

        # Get known groups for this location
        group_urls = []

        # Add location-specific groups
        if location.lower() in self.KNOWN_GROUPS:
            group_urls.extend(self.KNOWN_GROUPS[location.lower()])

        # Always add Hà Nội general groups
        group_urls.extend(self.KNOWN_GROUPS.get('hà nội', []))

        # Remove duplicates
        group_urls = list(set(group_urls))

        print(f"✅ Found {len(group_urls)} Facebook groups for {location}")

        # Also try Google search for more groups
        try:
            search_query = f"facebook groups bất động sản {location}"
            google_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"

            result = await self.crawl_url(google_url, css_selector='#search')

            if result and result.get('markdown'):
                discovered_urls = self._extract_group_urls(result['markdown'])

                for url in discovered_urls:
                    if url not in group_urls:
                        group_urls.append(url)

                print(f"✅ Discovered {len(discovered_urls)} more groups from Google")
        except Exception as e:
            print(f"  ⚠️ Google search error: {e}")

        # Crawl each group (max 3)
        all_listings = []

        for group_url in group_urls[:3]:
            try:
                listings = await self.crawl_single_group(group_url, query)
                all_listings.extend(listings)
            except Exception as e:
                print(f"  ⚠️ Error crawling {group_url}: {e}")
                continue

        print(f"✅ Total: {len(all_listings)} relevant posts from Facebook")

        return all_listings

    async def crawl_single_group(self, group_url: str, query: str) -> List[Dict]:
        """Crawl single Facebook group"""

        print(f"  📱 Crawling group: {group_url[:60]}...")

        # Crawl group page
        result = await self.crawl_url(url=group_url)

        if not result:
            return []

        # Parse with BeautifulSoup
        html = result.get('html', '')
        if not html:
            # Try markdown if no HTML
            markdown = result.get('markdown', '')
            return self._parse_markdown_posts(markdown, group_url, query)

        soup = BeautifulSoup(html, 'html.parser')
        posts = soup.select('[role="article"]')

        if not posts:
            # Fallback to markdown parsing
            markdown = result.get('markdown', '')
            return self._parse_markdown_posts(markdown, group_url, query)

        listings = []

        for post in posts[:10]:  # Top 10 posts
            try:
                listing = self._parse_facebook_post(post, group_url)

                # Filter relevant posts
                if listing and self._is_relevant_post(listing, query):
                    listings.append(listing)

            except Exception as e:
                continue

        print(f"    ✅ Extracted {len(listings)} relevant posts")

        return listings

    def _parse_facebook_post(self, post, group_url: str) -> Optional[Dict]:
        """Parse Facebook post to listing format"""

        # Extract text content
        content_elem = post.select_one('[data-ad-preview="message"]')
        if not content_elem:
            content_elem = post.select_one('[class*="text"], p, div[dir="auto"]')

        content = content_elem.get_text(strip=True) if content_elem else ''

        if not content or len(content) < 30:
            return None

        # Extract author
        author_elem = post.select_one('strong a, [class*="author"], h2 a')
        author = author_elem.get_text(strip=True) if author_elem else ''

        # Extract post URL
        link_elem = post.select_one('a[href*="/posts/"], a[href*="/permalink/"]')
        post_url = link_elem.get('href') if link_elem else group_url

        # Extract images
        img_elems = post.select('img[src*="fbcdn"], img[src*="facebook"]')
        images = [img.get('src') for img in img_elems if img.get('src')][:5]

        # Extract timestamp
        time_elem = post.select_one('abbr, [class*="timestamp"]')
        timestamp = time_elem.get('title') if time_elem else None

        return {
            'title': content[:100] + ('...' if len(content) > 100 else ''),
            'content': content,
            'description': content,
            'author': author,
            'contact_name': author,
            'source_url': post_url if post_url.startswith('http') else f"https://facebook.com{post_url}",
            'images': images,
            'timestamp': timestamp,
            'source_platform': 'facebook',
            'price': self._extract_price_from_content(content),
            'area': self._extract_area_from_content(content),
            'location': self._extract_location_from_content(content),
        }

    def _parse_markdown_posts(self, markdown: str, group_url: str, query: str) -> List[Dict]:
        """Parse posts from markdown content"""

        listings = []

        # Split by common post patterns
        # Look for text blocks that might be posts
        blocks = re.split(r'\n{2,}', markdown)

        for block in blocks:
            block = block.strip()

            if len(block) < 50:
                continue

            # Check if it looks like a property listing
            if not self._is_property_related(block):
                continue

            listing = {
                'title': block[:100] + ('...' if len(block) > 100 else ''),
                'content': block,
                'description': block,
                'source_url': group_url,
                'source_platform': 'facebook',
                'price': self._extract_price_from_content(block),
                'area': self._extract_area_from_content(block),
                'location': self._extract_location_from_content(block),
                'images': [],
            }

            if self._is_relevant_post(listing, query):
                listings.append(listing)

        return listings[:10]

    def _is_property_related(self, text: str) -> bool:
        """Check if text is property-related"""
        text_lower = text.lower()

        property_keywords = [
            'bán', 'cho thuê', 'cần bán', 'm2', 'm²', 'tỷ', 'triệu',
            'căn hộ', 'nhà', 'chung cư', 'đất', 'phòng ngủ', 'pn',
            'diện tích', 'giá', 'liên hệ', 'hotline'
        ]

        return any(kw in text_lower for kw in property_keywords)

    def _is_relevant_post(self, post: Dict, query: str) -> bool:
        """Check if post is relevant to query"""

        content = post.get('content', '').lower()

        # Must contain property keywords
        property_keywords = ['bán', 'cho thuê', 'cần bán', 'm2', 'tỷ', 'triệu', 'căn hộ', 'nhà']
        has_property = any(kw in content for kw in property_keywords)

        if not has_property:
            return False

        # Check location match from query
        query_lower = query.lower()

        # Common Hanoi districts
        location_keywords = [
            'cầu giấy', 'ba đình', 'đống đa', 'tây hồ', 'hoàn kiếm',
            'thanh xuân', 'hà đông', 'long biên', 'hoàng mai', 'nam từ liêm',
            'bắc từ liêm', 'hai bà trưng'
        ]

        for loc in location_keywords:
            if loc in query_lower and loc in content:
                return True

        # If no specific location in query, accept any property post
        has_location_in_query = any(loc in query_lower for loc in location_keywords)
        if not has_location_in_query:
            return True

        return False

    def _extract_group_urls(self, markdown: str) -> List[str]:
        """Extract Facebook group URLs from markdown"""

        url_pattern = r'https://www\.facebook\.com/groups/[\w.-]+'
        matches = re.findall(url_pattern, markdown)

        return list(set(matches))

    def _extract_location(self, query: str) -> str:
        """Extract location from query"""

        locations = {
            'cầu giấy': 'Cầu Giấy',
            'ba đình': 'Ba Đình',
            'đống đa': 'Đống Đa',
            'hoàn kiếm': 'Hoàn Kiếm',
            'tây hồ': 'Tây Hồ',
            'thanh xuân': 'Thanh Xuân',
            'hà đông': 'Hà Đông',
            'long biên': 'Long Biên',
            'hoàng mai': 'Hoàng Mai',
            'nam từ liêm': 'Nam Từ Liêm',
            'bắc từ liêm': 'Bắc Từ Liêm',
            'hai bà trưng': 'Hai Bà Trưng',
        }

        query_lower = query.lower()

        for key, value in locations.items():
            if key in query_lower:
                return value

        return 'Hà Nội'

    def _extract_price_from_content(self, content: str) -> str:
        """Extract price from content text"""

        patterns = [
            r'(\d+(?:[.,]\d+)?\s*tỷ)',
            r'(\d+(?:[.,]\d+)?\s*triệu)',
            r'giá\s*:?\s*(\d+(?:[.,]\d+)?(?:\s*tỷ|\s*triệu)?)',
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return ''

    def _extract_area_from_content(self, content: str) -> str:
        """Extract area from content text"""

        patterns = [
            r'(\d+(?:[.,]\d+)?\s*m[2²])',
            r'dt\s*:?\s*(\d+(?:[.,]\d+)?)',
            r'diện tích\s*:?\s*(\d+(?:[.,]\d+)?)',
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return ''

    def _extract_location_from_content(self, content: str) -> str:
        """Extract location from content text"""

        # Common Hanoi districts
        districts = [
            'cầu giấy', 'ba đình', 'đống đa', 'tây hồ', 'hoàn kiếm',
            'thanh xuân', 'hà đông', 'long biên', 'hoàng mai', 'nam từ liêm',
            'bắc từ liêm', 'hai bà trưng'
        ]

        content_lower = content.lower()

        for district in districts:
            if district in content_lower:
                return district.title()

        return ''

    async def crawl_marketplace(self, query: str) -> List[Dict]:
        """Crawl Facebook Marketplace"""

        print(f"\n🛒 Facebook Marketplace Search: {query}")

        # Build marketplace URL
        location = self._extract_location(query)
        marketplace_url = f"https://www.facebook.com/marketplace/hanoi/propertyrentals"

        result = await self.crawl_url(marketplace_url)

        if not result:
            return []

        # Parse listings
        listings = []
        soup = BeautifulSoup(result.get('html', ''), 'html.parser')

        items = soup.select('[data-testid="marketplace-card"], [class*="marketplace"]')

        for item in items[:10]:
            try:
                title_elem = item.select_one('span[dir="auto"]')
                price_elem = item.select_one('[aria-label*="₫"], [class*="price"]')
                link_elem = item.select_one('a')

                listing = {
                    'title': title_elem.get_text(strip=True) if title_elem else '',
                    'price': price_elem.get_text(strip=True) if price_elem else '',
                    'source_url': link_elem.get('href') if link_elem else '',
                    'source_platform': 'facebook_marketplace',
                }

                if listing['title']:
                    listings.append(listing)

            except Exception:
                continue

        print(f"✅ Found {len(listings)} marketplace listings")

        return listings
