"""Test search API endpoint"""
import asyncio
import httpx

async def test_api():
    print("Testing API search endpoint...\n")

    async with httpx.AsyncClient(timeout=180.0) as client:
        print("1. Health check...")
        r = await client.get("http://localhost:8001/health")
        print(f"   Status: {r.status_code} - {r.json()}\n")

        print("2. Search API (may take 30-60s)...")
        payload = {"query": "chung cư Hà Nội 2 phòng ngủ"}

        r = await client.post(
            "http://localhost:8001/api/v1/search",
            json=payload
        )

        print(f"   Status: {r.status_code}")

        if r.status_code == 200:
            data = r.json()
            print(f"   Listings found: {len(data.get('listings', []))}")
            print(f"   Sources: {data.get('sources', [])}")

            for i, l in enumerate(data.get('listings', [])[:3]):
                print(f"\n   {i+1}. {l.get('title', 'N/A')[:50]}")
                print(f"      Price: {l.get('price_text')}")
                print(f"      Area: {l.get('area_m2')} m2")
        else:
            print(f"   Error: {r.text[:500]}")

if __name__ == "__main__":
    asyncio.run(test_api())
