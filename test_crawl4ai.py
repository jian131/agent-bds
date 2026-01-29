"""
Quick test script for Crawl4AI migration
"""

import asyncio
from services.search_service import RealEstateSearchService

async def test_crawl4ai():
    """Test Crawl4AI search"""

    print("="*60)
    print("🧪 TEST CRAWL4AI MIGRATION")
    print("="*60)

    service = RealEstateSearchService()

    # Test query
    query = "chung cư 2 phòng ngủ cầu giấy 2-3 tỷ"

    print(f"\n📝 Query: {query}\n")

    try:
        results = await service.search(query, max_results=20)

        print(f"\n{'='*60}")
        print(f"✅ SUCCESS - Found {len(results)} listings")
        print(f"{'='*60}\n")

        if results:
            print("📋 Sample results:")
            for i, listing in enumerate(results[:3], 1):
                print(f"\n{i}. {listing['title'][:70]}")
                print(f"   💰 {listing['price_text']}")
                print(f"   📍 {listing['location']['address'][:50]}")
                print(f"   🌐 {listing['source_platform']}")

        return True

    except Exception as e:
        print(f"\n{'='*60}")
        print(f"❌ ERROR")
        print(f"{'='*60}")
        print(f"{e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_crawl4ai())
    exit(0 if success else 1)
