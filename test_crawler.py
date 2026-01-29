"""Test crawler directly"""
import asyncio
import sys
sys.path.insert(0, '.')

from crawlers.platform_crawlers import PlatformCrawler

async def test():
    crawler = PlatformCrawler()

    urls = [
        "https://batdongsan.com.vn/ban-can-ho-chung-cu-quan-cau-giay",
        "https://mogi.vn/mua-can-ho/ha-noi",
    ]

    for url in urls:
        print(f"\n{'='*60}")
        print(f"Testing: {url[:60]}...")
        print('='*60)

        try:
            results = await crawler.crawl_listing_page(url)
            print(f"✅ Found {len(results)} listings")

            if results:
                for i, r in enumerate(results[:2], 1):
                    print(f"\n  [{i}] {r.get('title', 'N/A')[:50]}...")
                    print(f"      Price: {r.get('price_text', 'N/A')}")
                    print(f"      Location: {r.get('location', {})}")
        except Exception as e:
            print(f"❌ Error: {e}")

    await crawler.close()

asyncio.run(test())
