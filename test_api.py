"""Quick API test script"""
import asyncio
import httpx

async def test_api():
    async with httpx.AsyncClient(timeout=120.0) as client:
        print("Testing search API...")

        response = await client.post(
            "http://localhost:8000/api/v1/search",
            json={
                "query": "chung cu 2PN Ha Noi",
                "search_realtime": True,
                "max_results": 5
            }
        )

        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Total results: {data.get('total', 0)}")
        print(f"Sources: {data.get('sources', [])}")
        print(f"Execution time: {data.get('execution_time_ms', 0)}ms")

        for i, result in enumerate(data.get("results", [])[:3]):
            print(f"\n{i+1}. {result.get('title', 'No title')[:60]}")
            print(f"   Price: {result.get('price_text', 'N/A')}")
            print(f"   Source: {result.get('source_platform', 'N/A')}")

if __name__ == "__main__":
    asyncio.run(test_api())
