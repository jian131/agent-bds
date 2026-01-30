"""Quick API test script"""
import asyncio
import httpx

BASE_URL = "http://127.0.0.1:8000"

async def test_api():
    async with httpx.AsyncClient(timeout=10.0) as client:
        print("=" * 60)
        print("🧪 BDS Agent API Test")
        print("=" * 60)

        # Test 1: Health check
        print("\n1️⃣ Testing /health...")
        try:
            r = await client.get(f"{BASE_URL}/health")
            print(f"   Status: {r.status_code}")
            print(f"   Response: {r.json()}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

        # Test 2: Get platforms
        print("\n2️⃣ Testing /api/v1/platforms...")
        try:
            r = await client.get(f"{BASE_URL}/api/v1/platforms")
            print(f"   Status: {r.status_code}")
            data = r.json()
            if isinstance(data, list):
                print(f"   Platforms: {len(data)} registered")
                for p in data[:5]:
                    print(f"      - {p.get('id', p)}")
                if len(data) > 5:
                    print(f"      ... and {len(data) - 5} more")
        except Exception as e:
            print(f"   ❌ Error: {e}")

        # Test 3: Search endpoint
        print("\n3️⃣ Testing /api/v1/search/multi (dry-run)...")
        try:
            r = await client.get(
                f"{BASE_URL}/api/v1/search/multi",
                params={"q": "nhà phố", "city": "Hanoi", "limit": 5}
            )
            print(f"   Status: {r.status_code}")
            if r.status_code == 200:
                data = r.json()
                print(f"   Response keys: {list(data.keys()) if isinstance(data, dict) else 'array'}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

        print("\n" + "=" * 60)
        print("✅ API Test Complete!")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_api())
