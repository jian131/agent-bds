"""Test search flow with direct URLs (bypassing Google)"""
import asyncio

async def test_search_direct():
    print("Testing search service with direct platform URLs...\n")
    test_urls = [
        'https://batdongsan.com.vn/ban-can-ho-chung-cu-ha-noi'
    ]

    query = "chung cư 2 phòng ngủ Hà Nội"

    print(f"Query: {query}")
    print(f"Direct URLs: {test_urls}")
    print()

    # Step 1: Crawl platforms directly
    print("Step 1: Crawling platform...")
    from crawlers.platform_crawlers import PlatformCrawler
    crawler = PlatformCrawler()

    raw_results = await crawler.crawl_listing_page(test_urls[0])
    print(f"   Found {len(raw_results)} raw listings")

    # Step 2: Parse
    print("\nStep 2: Parsing listings...")
    from parsers.listing_parser import ListingParser
    parser = ListingParser()
    parsed = await parser.parse_and_validate_batch(raw_results)
    print(f"   Parsed {len(parsed)} valid listings")

    # Step 3: Show results
    print("\n" + "="*60)
    print("SEARCH RESULTS")
    print("="*60)

    for i, listing in enumerate(parsed[:5], 1):
        print(f"\n{i}. {listing.get('title', 'N/A')[:60]}")
        print(f"   Price: {listing.get('price_text', 'N/A')}")
        print(f"   Area: {listing.get('area_m2', 'N/A')} m2")
        print(f"   Location: {listing.get('location', {}).get('district', 'N/A')}, {listing.get('location', {}).get('city', 'N/A')}")
        print(f"   URL: {listing.get('url', 'N/A')[:60]}...")

    print(f"\n{'='*60}")
    print(f"Total: {len(parsed)} listings found")

if __name__ == "__main__":
    asyncio.run(test_search_direct())
