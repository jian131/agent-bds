"""Simplified server + test - runs tests after short delay"""
import subprocess
import sys
import time
import threading
import requests

BASE_URL = "http://127.0.0.1:8000"

def run_server():
    """Run uvicorn server"""
    subprocess.run([
        sys.executable, "-c",
        "import uvicorn; uvicorn.run('api.main:app', host='127.0.0.1', port=8000, log_level='warning')"
    ], cwd=".", stderr=subprocess.DEVNULL)

def test_api():
    """Test API endpoints"""
    results = []

    # Test 1: Health check
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=10)
        results.append(f"1. /health: {r.status_code} - {r.json().get('status')}")
    except Exception as e:
        results.append(f"1. /health: ERROR - {e}")
        return results

    # Test 2: Get platforms
    try:
        r = requests.get(f"{BASE_URL}/api/v1/platforms", timeout=5)
        data = r.json()
        results.append(f"2. /api/v1/platforms: {r.status_code} - {data.get('total_count')} platforms")
        for p in data.get('platforms', []):
            results.append(f"   - {p.get('id')}: {p.get('name')}")
    except Exception as e:
        results.append(f"2. /api/v1/platforms: ERROR - {e}")

    # Test 3: Multi-platform search
    try:
        r = requests.get(
            f"{BASE_URL}/api/v1/search/multi",
            params={"q": "nhà phố", "city": "Hà Nội"},
            timeout=30
        )
        data = r.json()
        results.append(f"3. /api/v1/search/multi: {r.status_code}")
        if isinstance(data, dict):
            results.append(f"   Total: {data.get('total_listings', 0)} listings")
            results.append(f"   Platforms: {data.get('platforms_successful', 0)} OK, {data.get('platforms_blocked', 0)} blocked")
    except Exception as e:
        results.append(f"3. /api/v1/search/multi: ERROR - {e}")

    return results

if __name__ == "__main__":
    # Start server in background thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Wait for server to start
    print("Starting server...")
    time.sleep(8)

    # Run tests
    print("\n=== API Test Results ===\n")
    for line in test_api():
        print(line)

    print("\n=== Done ===")
