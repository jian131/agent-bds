"""
Main search service using Crawl4AI
Orchestrates: Google search → Platform crawling → Facebook → Parsing → Storage
"""

import asyncio
from typing import List, Dict, AsyncGenerator, Optional
from crawlers.google_crawler import GoogleSearchCrawler
from crawlers.platform_crawlers import PlatformCrawler
from crawlers.facebook_crawler import FacebookCrawler
from parsers.listing_parser import ListingParser
from storage.database import ListingCRUD, get_session
from storage.vector_db import get_vector_db
from storage.sheets import GoogleSheetsClient
import time
import json

class RealEstateSearchService:
    """Fast search service with Crawl4AI"""

    def __init__(self):
        self.google_crawler = GoogleSearchCrawler()
        self.platform_crawler = PlatformCrawler()
        self.facebook_crawler = FacebookCrawler()
        self.parser = ListingParser()
        self.listing_crud = ListingCRUD()
        self._vector_db = None  # Lazy init
        self.sheets = GoogleSheetsClient()

    @property
    def vector_db(self):
        """Lazy load vector DB - returns None if unavailable"""
        if self._vector_db is None:
            self._vector_db = get_vector_db()
        return self._vector_db

    async def search_stream(self, user_query: str, max_results: int = 50) -> AsyncGenerator[Dict, None]:
        """
        Streaming search - yields progress updates and results

        Yields:
            Dict with: type (status/result/complete), data
        """

        start_time = time.time()

        yield {'type': 'status', 'message': 'Searching Google...'}

        # Step 1: Google search with timeout
        try:
            urls_data = await asyncio.wait_for(
                self.google_crawler.search_properties(query=user_query, max_results=15),
                timeout=15.0
            )
        except asyncio.TimeoutError:
            yield {'type': 'status', 'message': 'Google timeout - using direct platform search'}
            urls_data = []
        except Exception as e:
            yield {'type': 'status', 'message': f'Google error - using fallback'}
            urls_data = []

        # Fallback: direct platform URLs
        if not urls_data:
            urls_data = self._generate_fallback_urls(user_query)
            yield {'type': 'status', 'message': f'Searching {len(urls_data)} platforms directly'}

        if not urls_data:
            yield {'type': 'complete', 'total': 0, 'time': time.time() - start_time}
            return

        yield {'type': 'status', 'message': f'Found {len(urls_data)} sources'}

        # Step 2: Crawl platforms
        all_raw_listings = []

        platforms_crawled = set()
        for data in urls_data:
            platform = data.get('platform', 'unknown')
            if platform not in platforms_crawled:
                yield {'type': 'status', 'message': f'Crawling {platform}...'}
                platforms_crawled.add(platform)

        crawl_tasks = [
            self.platform_crawler.crawl_listing_page(data['url'])
            for data in urls_data
        ]

        crawl_results = await asyncio.gather(*crawl_tasks, return_exceptions=True)

        for result in crawl_results:
            if isinstance(result, list):
                all_raw_listings.extend(result)

        yield {'type': 'status', 'message': f'Crawled {len(all_raw_listings)} listings'}

        # Step 2.5: Facebook groups (with short timeout)
        yield {'type': 'status', 'message': 'Searching Facebook...'}

        try:
            facebook_listings = await asyncio.wait_for(
                self.facebook_crawler.crawl_facebook_groups(user_query),
                timeout=10.0
            )
            all_raw_listings.extend(facebook_listings)
            yield {'type': 'status', 'message': f'Found {len(facebook_listings)} Facebook posts'}
        except asyncio.TimeoutError:
            yield {'type': 'status', 'message': 'Facebook timeout - skipping'}
        except Exception as e:
            yield {'type': 'status', 'message': f'Facebook skipped'}

        # Step 3: Parse
        yield {'type': 'status', 'message': 'Parsing results...'}

        validated_listings = await self.parser.parse_and_validate_batch(all_raw_listings)
        unique_listings = self._deduplicate(validated_listings)

        # Yield results one by one for progressive loading
        for listing in unique_listings[:max_results]:
            yield {'type': 'result', 'data': self._serialize_listing(listing)}

        elapsed = time.time() - start_time
        yield {
            'type': 'complete',
            'total': len(unique_listings),
            'time': elapsed,
            'platforms': list(platforms_crawled)
        }

    def _serialize_listing(self, listing: Dict) -> Dict:
        """Serialize listing for JSON response"""

        # Convert datetime to string
        result = {}
        for key, value in listing.items():
            if key == 'scraped_at':
                result[key] = value.isoformat() if value else None
            elif key == 'raw_data':
                continue  # Skip raw data
            else:
                result[key] = value

        return result

    async def search(self, user_query: str, max_results: int = 50) -> List[Dict]:
        """
        Main search method (non-streaming)

        Flow:
        1. Google search → URLs
        2. Crawl URLs in parallel → Raw data
        3. Facebook groups → More data
        4. Parse & validate → Clean listings
        5. Save to DB → Return
        """

        print(f"\n{'='*60}")
        print(f"SEARCH: {user_query}")
        print(f"{'='*60}")

        start_time = time.time()

        # Step 1: Google search (with timeout)
        try:
            urls_data = await asyncio.wait_for(
                self.google_crawler.search_properties(query=user_query, max_results=15),
                timeout=15.0
            )
        except asyncio.TimeoutError:
            print("Google search timeout - using fallback URLs")
            urls_data = []
        except Exception as e:
            print(f"Google search error: {e} - using fallback URLs")
            urls_data = []

        # Fallback: direct platform URLs if Google returns nothing
        if not urls_data:
            urls_data = self._generate_fallback_urls(user_query)
            print(f"Using {len(urls_data)} fallback platform URLs")

        if not urls_data:
            print("No URLs found")
            return []

        print(f"\nWill crawl {len(urls_data)} URLs:")
        for i, data in enumerate(urls_data[:5], 1):
            print(f"  {i}. {data['platform']}: {data['url'][:70]}...")

        # Step 2: Crawl all URLs in parallel (FAST!)
        print(f"\nCrawling {len(urls_data)} URLs in parallel...")

        crawl_tasks = [
            self.platform_crawler.crawl_listing_page(data['url'])
            for data in urls_data
        ]

        crawl_results = await asyncio.gather(*crawl_tasks, return_exceptions=True)

        # Flatten results
        all_raw_listings = []
        for result in crawl_results:
            if isinstance(result, list):
                all_raw_listings.extend(result)
            elif isinstance(result, Exception):
                print(f"  Crawl error: {result}")

        print(f"\nCrawled {len(all_raw_listings)} raw listings")

        # Step 2.5: Also crawl Facebook groups (with timeout)
        print(f"\nSearching Facebook groups...")
        try:
            facebook_listings = await asyncio.wait_for(
                self.facebook_crawler.crawl_facebook_groups(user_query),
                timeout=10.0
            )
            all_raw_listings.extend(facebook_listings)
            print(f"Found {len(facebook_listings)} posts from Facebook")
        except asyncio.TimeoutError:
            print("Facebook timeout - skipping")
        except Exception as e:
            print(f"Facebook crawl error: {e}")

        if not all_raw_listings:
            print("⚠️ No listings extracted")
            return []

        # Step 3: Parse and validate
        print(f"\n🔍 Parsing and validating...")
        validated_listings = await self.parser.parse_and_validate_batch(all_raw_listings)

        print(f"✅ {len(validated_listings)} valid listings")

        # Step 4: Deduplicate
        unique_listings = self._deduplicate(validated_listings)
        print(f"✅ {len(unique_listings)} unique listings after deduplication")

        # Step 5: Save to storage (skip DB for now - no PostgreSQL running)
        # Storage saves disabled for demo - just return results
        print(f"\n⏭️ Storage skipped (demo mode)")

        elapsed = time.time() - start_time
        print(f"\n⏱️  Total time: {elapsed:.1f}s")
        print(f"⚡ Speed: {elapsed/max(len(unique_listings), 1):.2f}s per listing")

        return unique_listings[:max_results]

    def _deduplicate(self, listings: List[Dict]) -> List[Dict]:
        """Remove duplicate listings by ID"""

        seen_ids = set()
        unique = []

        for listing in listings:
            listing_id = listing.get('id')
            if listing_id and listing_id not in seen_ids:
                seen_ids.add(listing_id)
                unique.append(listing)

        return unique

    def _generate_fallback_urls(self, query: str) -> List[Dict]:
        """Generate direct platform URLs when Google search fails"""

        query_lower = query.lower()
        urls = []

        # Detect location
        is_hanoi = any(x in query_lower for x in ['hà nội', 'ha noi', 'hanoi', 'cầu giấy', 'đống đa', 'hai bà trưng'])
        is_hcm = any(x in query_lower for x in ['hồ chí minh', 'sài gòn', 'saigon', 'hcm', 'quận 1', 'quận 7'])

        # Detect property type
        is_apartment = any(x in query_lower for x in ['chung cư', 'căn hộ', 'apartment'])
        is_house = any(x in query_lower for x in ['nhà', 'house', 'biệt thự'])
        is_land = any(x in query_lower for x in ['đất', 'land'])

        # Build base path
        city_path = 'ha-noi' if is_hanoi else ('ho-chi-minh' if is_hcm else 'ha-noi')

        if is_apartment:
            property_path = 'ban-can-ho-chung-cu'
        elif is_house:
            property_path = 'ban-nha'
        elif is_land:
            property_path = 'ban-dat'
        else:
            property_path = 'ban-can-ho-chung-cu'  # Default to apartments

        # Batdongsan.com.vn (primary)
        urls.append({
            'url': f'https://batdongsan.com.vn/{property_path}-{city_path}',
            'platform': 'batdongsan.com.vn',
            'priority': 1
        })

        # Mogi.vn
        mogi_path = 'mua-can-ho' if is_apartment else ('mua-nha-dat' if is_house else 'mua-dat')
        urls.append({
            'url': f'https://mogi.vn/{mogi_path}/{city_path}',
            'platform': 'mogi.vn',
            'priority': 2
        })

        # Alonhadat
        urls.append({
            'url': f'https://alonhadat.com.vn/{property_path}/{city_path}.html',
            'platform': 'alonhadat.com.vn',
            'priority': 2
        })

        return urls

    async def health_check(self) -> Dict:
        """Check service health"""

        try:
            # Test LLM
            llm_test = await self.google_crawler.llm.ainvoke([{"role": "user", "content": "test"}])

            # Test database
            db_healthy = await self.db.health_check()

            return {
                'status': 'healthy',
                'llm': 'ok',
                'database': 'ok' if db_healthy else 'error',
                'service': 'crawl4ai-search',
                'version': '2.0'
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
