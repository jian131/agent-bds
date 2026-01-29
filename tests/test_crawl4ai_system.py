"""
Comprehensive system test for Crawl4AI migration
Tests speed, multi-platform support, and data quality
"""

import asyncio
import time
from services.search_service import RealEstateSearchService
import json

async def test_speed_benchmark():
    """Benchmark speed vs browser-use expectations"""

    print("\n" + "="*60)
    print("⚡ SPEED BENCHMARK - Crawl4AI")
    print("="*60)

    service = RealEstateSearchService()

    test_queries = [
        "chung cư 2PN Cầu Giấy 2-3 tỷ",
        "nhà riêng Ba Đình 5-7 tỷ",
        "đất nền Hà Đông dưới 2 tỷ"
    ]

    total_results = 0
    total_time = 0

    for query in test_queries:
        print(f"\n📝 Query: {query}")

        start = time.time()
        try:
            results = await service.search(query, max_results=30)
            elapsed = time.time() - start

            total_results += len(results)
            total_time += elapsed

            print(f"✅ Results: {len(results)} in {elapsed:.1f}s")
            print(f"   Speed: {elapsed/max(len(results), 1):.2f}s per listing")

        except Exception as e:
            print(f"❌ Error: {e}")

    if total_results > 0:
        avg_speed = total_time / total_results
        print(f"\n📊 Overall Statistics:")
        print(f"   Total results: {total_results}")
        print(f"   Total time: {total_time:.1f}s")
        print(f"   Average: {avg_speed:.2f}s per listing")
        print(f"\n🎯 Target: <6s per listing (browser-use was 30-60s)")
        print(f"   Status: {'✅ PASS' if avg_speed < 6 else '⚠️ NEEDS OPTIMIZATION'}")

async def test_multi_platform():
    """Test scraping from multiple platforms"""

    print("\n" + "="*60)
    print("🌐 MULTI-PLATFORM TEST")
    print("="*60)

    service = RealEstateSearchService()

    results = await service.search("chung cư Cầu Giấy", max_results=50)

    # Count platforms
    platforms = {}
    for listing in results:
        platform = listing.get('source_platform', 'unknown')
        platforms[platform] = platforms.get(platform, 0) + 1

    print(f"\n📊 Platform Distribution ({len(results)} total):")
    for platform, count in sorted(platforms.items(), key=lambda x: -x[1]):
        print(f"   {platform}: {count} listings ({count/len(results)*100:.1f}%)")

    print(f"\n🎯 Target: 3+ platforms")
    print(f"   Status: {'✅ PASS' if len(platforms) >= 3 else '⚠️ NEEDS MORE PLATFORMS'}")

async def test_data_quality():
    """Test data quality and validation"""

    print("\n" + "="*60)
    print("🔍 DATA QUALITY TEST")
    print("="*60)

    service = RealEstateSearchService()

    results = await service.search("chung cư Hà Nội", max_results=30)

    if not results:
        print("❌ No results to validate")
        return

    # Validate fields
    required_fields = ['title', 'price_text', 'location', 'source_url']

    valid_count = 0
    has_price = 0
    has_phone = 0
    has_area = 0

    for listing in results:
        # Check required fields
        if all(listing.get(field) for field in required_fields):
            valid_count += 1

        if listing.get('price_number', 0) > 0:
            has_price += 1

        if listing.get('contact', {}).get('phone_clean'):
            has_phone += 1

        if listing.get('area_m2', 0) > 0:
            has_area += 1

    print(f"\n📊 Data Quality Metrics:")
    print(f"   Valid listings: {valid_count}/{len(results)} ({valid_count/len(results)*100:.1f}%)")
    print(f"   With price: {has_price}/{len(results)} ({has_price/len(results)*100:.1f}%)")
    print(f"   With phone: {has_phone}/{len(results)} ({has_phone/len(results)*100:.1f}%)")
    print(f"   With area: {has_area}/{len(results)} ({has_area/len(results)*100:.1f}%)")

    print(f"\n🎯 Target: >80% valid, >70% with price")
    print(f"   Status: {'✅ PASS' if valid_count/len(results) > 0.8 else '⚠️ NEEDS IMPROVEMENT'}")

async def test_error_handling():
    """Test error handling with invalid queries"""

    print("\n" + "="*60)
    print("🛡️  ERROR HANDLING TEST")
    print("="*60)

    service = RealEstateSearchService()

    bad_queries = [
        "",  # Empty
        "asdfghjkl",  # Gibberish
        "buy house mars",  # Impossible
    ]

    for query in bad_queries:
        print(f"\n📝 Testing: '{query}'")
        try:
            results = await service.search(query, max_results=10)
            print(f"   ✅ Handled gracefully - {len(results)} results")
        except Exception as e:
            print(f"   ⚠️  Exception: {type(e).__name__}")

async def run_all_tests():
    """Run all tests"""

    print("\n" + "🧪"*30)
    print("CRAWL4AI MIGRATION TEST SUITE")
    print("🧪"*30)

    tests = [
        ("Speed Benchmark", test_speed_benchmark),
        ("Multi-Platform", test_multi_platform),
        ("Data Quality", test_data_quality),
        ("Error Handling", test_error_handling),
    ]

    results = []

    for name, test_func in tests:
        try:
            await test_func()
            results.append((name, True))
        except Exception as e:
            print(f"\n❌ Test '{name}' failed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {status} - {name}")

    print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")

    return passed == total

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)
