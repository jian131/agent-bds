"""
Simple test - Crawl4AI without storage
"""

import asyncio
from crawlers.platform_crawlers import PlatformCrawler
from parsers.listing_parser import ListingParser

async def test_simple():
    """Test crawl without storage"""

    print("="*60)
    print("🧪 SIMPLE CRAWL4AI TEST")
    print("="*60)

    # Use test URLs directly (Google blocks crawlers)
    test_urls = [
        "https://batdongsan.com.vn/cho-thue-can-ho-chung-cu",
        "https://chotot.com/tp-ho-chi-minh/mua-ban-bat-dong-san",
        "https://mogi.vn/ha-noi/mua-chung-cu"
    ]

    print(f"\n📝 Testing with {len(test_urls)} URLs")

    # Step 1: Crawl URLs
    print("\n🕷️  Step 1: Crawl listings...")
    crawler = PlatformCrawler()

    raw_data = []
    for url in test_urls:
        print(f"  Crawling {url}...")
        result = await crawler.crawl_listing_page(url)
        if result:
            raw_data.extend(result if isinstance(result, list) else [result])

    print(f"Crawled {len(raw_data)} listings")

    # Step 2: Parse
    if raw_data:
        print("\n📝 Step 2: Parse data...")
        parser = ListingParser()
        listings = await parser.parse_and_validate_batch(raw_data)
        print(f"Parsed {len(listings)} valid listings")

        # Show results
        if listings:
            print(f"\n{'='*60}")
            print("✅ RESULTS")
            print(f"{'='*60}")
            for i, listing in enumerate(listings[:5], 1):
                print(f"\n{i}. {listing['title'][:70]}")
                print(f"   💰 {listing['price_text']}")
                print(f"   📐 {listing['area_text']}")
                print(f"   📍 {listing['location']['address'][:50]}")

        return len(listings) > 0
    else:
        print("\n⚠️  No data crawled")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_simple())
    exit(0 if success else 1)
