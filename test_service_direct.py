"""Test search service directly"""
import asyncio
import time

async def test():
    print("Testing RealEstateSearchService directly...\n")

    from services.search_service import RealEstateSearchService

    service = RealEstateSearchService()
    query = "chung cư Hà Nội 2 phòng ngủ"

    print(f"Query: {query}\n")

    start = time.time()
    results = await service.search(query, max_results=20)
    elapsed = time.time() - start

    print(f"\n{'='*60}")
    print(f"COMPLETED in {elapsed:.1f}s")
    print(f"Found {len(results)} listings")
    print(f"{'='*60}")

    for i, r in enumerate(results[:5]):
        print(f"\n{i+1}. {r.get('title', 'N/A')[:60]}")
        print(f"   Price: {r.get('price_text')}")
        print(f"   Area: {r.get('area_m2')} m2")

if __name__ == "__main__":
    asyncio.run(test())
