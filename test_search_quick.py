"""Quick search test - no VectorDB"""
import asyncio
from services.search_service import RealEstateSearchService

async def test():
    service = RealEstateSearchService()
    print("🔍 Testing search: chung cu 2PN Ha Noi...\n")

    results = await service.search("chung cu 2 phong ngu Ha Noi", max_results=5)

    print(f"\n✅ Found {len(results)} results\n")
    for i, r in enumerate(results[:5]):
        print(f"{i+1}. {r.get('title', 'N/A')[:60]}")
        print(f"   💰 {r.get('price_text', 'N/A')}")
        print(f"   📐 {r.get('area_m2', 'N/A')} m²")
        print(f"   🌐 {r.get('source_platform', 'N/A')}")
        print()

if __name__ == "__main__":
    asyncio.run(test())
