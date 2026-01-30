"""Quick sync test for API endpoints"""
import requests
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_api():
    print("=" * 60)
    print("🧪 BDS Agent API Test")
    print("=" * 60)

    # Test 1: Health check
    print("\n1️⃣ Testing /health...")
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"   ✅ Status: {r.status_code}")
        print(f"   Response: {r.json()}")
    except requests.exceptions.ConnectionError:
        print("   ❌ Connection refused - server not running!")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

    # Test 2: Get platforms
    print("\n2️⃣ Testing /api/v1/platforms...")
    try:
        r = requests.get(f"{BASE_URL}/api/v1/platforms", timeout=5)
        print(f"   ✅ Status: {r.status_code}")
        data = r.json()
        if isinstance(data, list):
            print(f"   Platforms: {len(data)} registered")
            for p in data:
                print(f"      - {p.get('id', p)}: {p.get('name', 'N/A')}")
        else:
            print(f"   Response: {data}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test 3: OpenAPI spec
    print("\n3️⃣ Testing /openapi.json...")
    try:
        r = requests.get(f"{BASE_URL}/openapi.json", timeout=5)
        print(f"   ✅ Status: {r.status_code}")
        data = r.json()
        paths = list(data.get("paths", {}).keys())
        print(f"   Available endpoints: {len(paths)}")
        for path in paths[:10]:
            print(f"      - {path}")
        if len(paths) > 10:
            print(f"      ... and {len(paths) - 10} more")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    print("\n" + "=" * 60)
    print("✅ API Test Complete!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_api()
    sys.exit(0 if success else 1)
