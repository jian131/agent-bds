"""Test platform crawler directly"""
import asyncio
from crawlers.platform_crawlers import PlatformCrawler
from parsers.listing_parser import ListingParser

async def test():
    crawler = PlatformCrawler()
    parser = ListingParser()

    url = 'https://batdongsan.com.vn/ban-can-ho-chung-cu-ha-noi'

    print('Testing platform crawler...\n')
    raw_results = await crawler.crawl_listing_page(url)
    print(f'Found {len(raw_results)} raw listings')

    # Show raw results first
    print('\nRaw results sample:')
    for i, r in enumerate(raw_results[:3]):
        print(f"  {i+1}. {r.get('title', 'N/A')[:50]}")
        print(f"     Price: {r.get('price', 'N/A')}")
        print(f"     Area: {r.get('area', 'N/A')}")

    print('\nParsing with ListingParser...')
    parsed = await parser.parse_and_validate_batch(raw_results)
    print(f'Parsed {len(parsed)} valid listings\n')

    for i, r in enumerate(parsed[:5]):
        print(f"{i+1}. {r.get('title', 'N/A')[:55]}")
        print(f"   Price: {r.get('price_text', 'N/A')}")
        print(f"   Area: {r.get('area_m2', 'N/A')} m2")
        print(f"   Location: {r.get('location', {}).get('district', 'N/A')}")
