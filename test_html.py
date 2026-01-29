# -*- coding: utf-8 -*-
"""Test HTML selectors"""
import asyncio
import sys
sys.path.insert(0, '.')

from crawlers.base_crawler import BaseCrawler
from bs4 import BeautifulSoup

async def test():
    crawler = BaseCrawler()
    # Test with price filter
    url = 'https://batdongsan.com.vn/ban-can-ho-chung-cu-quan-cau-giay?gia_tu=1.6&gia_den=2.5'
    print(f'Testing URL: {url}')

    result = await crawler.crawl_url(
        url=url,
        css_selector='.js__product-link-for-product-id',
        wait_for='.js__product-link-for-product-id'
    )
    if result:
        soup = BeautifulSoup(result['html'], 'html.parser')
        items = soup.select('.js__product-link-for-product-id')
        print(f'Found {len(items)} items\n')

        for i, item in enumerate(items[:8], 1):
            title = item.select_one('.re__card-title')
            price = item.select_one('.re__card-config-price')
            location = item.select_one('.re__card-location')

            t = title.get_text(strip=True)[:45] if title else 'N/A'
            p = price.get_text(strip=True) if price else 'N/A'
            l = location.get_text(strip=True) if location else 'N/A'

            print(f'{i}. {t}')
            print(f'   Price: {p} | Loc: {l}')
            print()

asyncio.run(test())
