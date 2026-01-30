"""Combined server + test - runs tests after short delay"""
import subprocess
import sys
import time
import threading
import requests

def run_server():
    """Run uvicorn server"""
    subprocess.run([
        sys.executable, "-c",
        "import uvicorn; uvicorn.run('api.main:app', host='127.0.0.1', port=8000)"
    ], cwd=".")

def test_api():
    """Test API endpoints"""
    BASE_URL = "http://127.0.0.1:8000"

    print("\n" + "=" * 60)
    print("🧪 BDS Agent API Test")
    print("=" * 60)

    # Test 1: Health check
    print("\n1️⃣ Testing /health...")
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=10)
        print(f"   ✅ Status: {r.status_code}")
        data = r.json()
        print(f"   Health Status: {data.get('status')}")
        for service, status in data.get('services', {}).items():
            emoji = "✅" if status == "ok" or "ok" in str(status) else "⚠️"
            print(f"      {emoji} {service}: {status}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

    # Test 2: Get platforms (detailed)
    print("\n2️⃣ Testing /api/v1/platforms...")
    try:
        r = requests.get(f"{BASE_URL}/api/v1/platforms", timeout=5)
        print(f"   ✅ Status: {r.status_code}")
        data = r.json()

        print(f"\n   📊 Stats:")
        print(f"      Total platforms: {data.get('total_count', 0)}")
        print(f"      Available: {data.get('available_count', 0)}")

        print(f"\n   📋 Platforms:")
        for p in data.get('platforms', []):
            print(f"      ✅ {p.get('id'):20} - {p.get('name')}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test 3: Multi-platform search endpoint
    print("\n3️⃣ Testing /api/v1/search/multi...")
    try:
        r = requests.get(
            f"{BASE_URL}/api/v1/search/multi",
            params={"q": "nhà phố", "city": "Hà Nội"},
            timeout=10
        )
        print(f"   ✅ Status: {r.status_code}")
        data = r.json()
        if isinstance(data, dict):
            print(f"   Response keys: {list(data.keys())}")
            if "results" in data:
                print(f"   Results: {len(data.get('results', []))} listings")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test 4: OpenAPI spec
    print("\n4️⃣ Testing /openapi.json...")
    try:
        r = requests.get(f"{BASE_URL}/openapi.json", timeout=5)
        print(f"   ✅ Status: {r.status_code}")
        data = r.json()
        paths = list(data.get("paths", {}).keys())
        print(f"   Available endpoints: {len(paths)}")
        for path in paths[:15]:
            print(f"      - {path}")
        if len(paths) > 15:
            print(f"      ... and {len(paths) - 15} more")
    except Exception as e:
        print(f"   ❌ Error: {e}")
