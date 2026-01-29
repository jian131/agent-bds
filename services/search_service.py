"""
Main search service using Crawl4AI
Orchestrates: Google search → Platform crawling → Facebook → Parsing → Storage
"""

import asyncio
from typing import List, Dict, AsyncGenerator
from crawlers.google_crawler import GoogleSearchCrawler
from crawlers.platform_crawlers import PlatformCrawler
from crawlers.facebook_crawler import FacebookCrawler
from parsers.listing_parser import ListingParser
from storage.database import ListingCRUD, get_session
from storage.vector_db import VectorDB
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
        self.vector_db = VectorDB()
        self.sheets = GoogleSheetsClient()

    async def search_stream(self, user_query: str, max_results: int = 50) -> AsyncGenerator[Dict, None]:
        """
        Streaming search - yields progress updates and results

        Yields:
            Dict with: type (status/result/complete), data
        """

        start_time = time.time()

        yield {'type': 'status', 'message': '🔍 Đang tìm kiếm trên Google...'}

        # Step 1: Google search
        urls_data = await self.google_crawler.search_properties(
            query=user_query,
            max_results=15
        )

        if not urls_data:
            yield {'type': 'status', 'message': '⚠️ Không tìm thấy URLs từ Google'}
            yield {'type': 'complete', 'total': 0, 'time': time.time() - start_time}
            return

        yield {'type': 'status', 'message': f'✅ Tìm thấy {len(urls_data)} URLs từ nhiều nguồn'}

        # Step 2: Crawl platforms
        all_raw_listings = []

        platforms_crawled = set()
        for data in urls_data:
            platform = data.get('platform', 'unknown')
            if platform not in platforms_crawled:
                yield {'type': 'status', 'message': f'📄 Đang crawl {platform}...'}
                platforms_crawled.add(platform)

        crawl_tasks = [
            self.platform_crawler.crawl_listing_page(data['url'])
            for data in urls_data
        ]

        crawl_results = await asyncio.gather(*crawl_tasks, return_exceptions=True)

        for result in crawl_results:
            if isinstance(result, list):
                all_raw_listings.extend(result)

        yield {'type': 'status', 'message': f'✅ Đã crawl {len(all_raw_listings)} listings từ websites'}

        # Step 2.5: Facebook groups
        yield {'type': 'status', 'message': '🔵 Đang tìm kiếm Facebook groups...'}

        try:
            facebook_listings = await self.facebook_crawler.crawl_facebook_groups(user_query)
            all_raw_listings.extend(facebook_listings)
            yield {'type': 'status', 'message': f'✅ Tìm thấy {len(facebook_listings)} posts từ Facebook'}
        except Exception as e:
            yield {'type': 'status', 'message': f'⚠️ Facebook error: {str(e)[:50]}'}

        # Step 3: Parse
        yield {'type': 'status', 'message': '🔍 Đang phân tích và lọc kết quả...'}

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
        print(f"🏠 SEARCH: {user_query}")
        print(f"{'='*60}")

        start_time = time.time()

        # Step 1: Google search
        urls_data = await self.google_crawler.search_properties(
            query=user_query,
            max_results=15
        )

        if not urls_data:
            print("⚠️ No URLs found from Google")
            return []

        print(f"\n📋 Will crawl {len(urls_data)} URLs:")
        for i, data in enumerate(urls_data[:5], 1):
            print(f"  {i}. {data['platform']}: {data['url'][:70]}...")

        # Step 2: Crawl all URLs in parallel (FAST!)
        print(f"\n🚀 Crawling {len(urls_data)} URLs in parallel...")

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
                print(f"  ⚠️ Crawl error: {result}")

        print(f"\n✅ Crawled {len(all_raw_listings)} raw listings")

        # Step 2.5: Also crawl Facebook groups
        print(f"\n🔵 Searching Facebook groups...")
        try:
            facebook_listings = await self.facebook_crawler.crawl_facebook_groups(user_query)
            all_raw_listings.extend(facebook_listings)
            print(f"✅ Found {len(facebook_listings)} posts from Facebook")
        except Exception as e:
            print(f"⚠️ Facebook crawl error: {e}")

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

        # Step 5: Save to storage
        if unique_listings:
            print(f"\n💾 Saving to storage...")
            try:
                # Save to database
                async with get_session() as session:
                    for listing in unique_listings:
                        await self.listing_crud.create_listing(session, listing)
                print(f"  ✅ Saved to PostgreSQL")

                # Save to vector DB for semantic search
                await self.vector_db.add_listings(unique_listings)
                print(f"  ✅ Saved to ChromaDB")

                # Save to Google Sheets
                await self.sheets.append_listings(unique_listings)
                print(f"  ✅ Saved to Google Sheets")

            except Exception as e:
                print(f"  ⚠️ Storage error: {e}")

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
