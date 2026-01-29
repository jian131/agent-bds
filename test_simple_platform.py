"""Simple test for platform crawler"""
import asyncio

async def test():
    print("1. Testing crawl_url directly...")

    from crawlers.base_crawler import BaseCrawler
    from crawlers.css_selectors import get_selectors, detect_platform

    crawler = BaseCrawler()
    url = 'https://batdongsan.com.vn/ban-can-ho-chung-cu-ha-noi'

    # Get selectors
    platform = detect_platform(url)
    selectors = get_selectors(url, 'list_page')

    print(f"   Platform: {platform}")
    print(f"   Items selector: {selectors.get('items', 'N/A')}")

    print("\n2. Crawling with css_selector...")
    items_selector = selectors.get('items', 'body')

    result = await crawler.crawl_url(
        url=url,
        css_selector=items_selector,
        wait_for=items_selector
    )

    if result:
        print(f"   Success! HTML length: {len(result.get('html', ''))}")

        # Parse with BeautifulSoup
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(result['html'], 'html.parser')
        items = soup.select(items_selector)
        print(f"   Found {len(items)} items in HTML")

        if items:
            schema = selectors.get('schema', {})
            first = items[0]
            print("\n   First item fields:")
            for field, sel in list(schema.items())[:3]:
                if '::text' in sel:
                    s = sel.replace('::text', '')
                    elem = first.select_one(s)
                    val = elem.get_text(strip=True)[:40] if elem else 'N/A'
                    print(f"   - {field}: {val}")
    else:
        print("   Failed!")

if __name__ == "__main__":
    asyncio.run(test())
