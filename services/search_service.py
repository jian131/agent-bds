"""
Main search service using Crawl4AI
Orchestrates: Google search → Platform crawling → Parsing → Storage
"""

import asyncio
from typing import List, Dict
from crawlers.google_crawler import GoogleSearchCrawler
from crawlers.platform_crawlers import PlatformCrawler
from parsers.listing_parser import ListingParser
from storage.database import Database
from storage.vector_db import VectorDB
from storage.sheets import SheetsStorage
import time

class RealEstateSearchService:
    """Fast search service with Crawl4AI"""

    def __init__(self):
        self.google_crawler = GoogleSearchCrawler()
        self.platform_crawler = PlatformCrawler()
        self.parser = ListingParser()
        self.db = Database()
        self.vector_db = VectorDB()
        self.sheets = SheetsStorage()

    async def search(self, user_query: str, max_results: int = 50) -> List[Dict]:
        """
        Main search method

        Flow:
        1. Google search → URLs
        2. Crawl URLs in parallel → Raw data
        3. Parse & validate → Clean listings
        4. Save to DB → Return
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
                await self.db.save_listings(unique_listings)
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
