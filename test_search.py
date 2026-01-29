# -*- coding: utf-8 -*-
"""Test search service directly"""
import asyncio
import sys
sys.path.insert(0, '.')

from services.search_service import RealEstateSearchService

async def test():
    service = RealEstateSearchService()
    # Test with wider price - "5 ty" (more listings available)
    results = await service.search('chung cu 5 ty ha noi', max_results=10)
    print(f'\n\nFinal results: {len(results)}')
    for r in results[:5]:
        title = r.get('title', 'N/A')[:50]
        price = r.get('price_text', 'N/A')
        loc = r.get('location', 'N/A')
        if isinstance(loc, dict):
            loc = loc.get('address', 'N/A')
        print(f'  - {title}')
        print(f'    Price: {price} | Loc: {loc}')

asyncio.run(test())
