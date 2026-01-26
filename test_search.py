"""
Test script for BDS Agent - Google-First Multi-Platform Search
"""
import asyncio
import json
import sys
from datetime import datetime
from agents.search_agent import RealEstateSearchAgent
from config import settings

async def test_google_first_search():
    """Test the Google-first search strategy with multi-platform scraping."""
    print("=" * 60)
    print("🏠 BDS AGENT - GOOGLE-FIRST SEARCH TEST")
    print("=" * 60)
    print(f"📌 LLM Mode: {settings.llm_mode}")
    print(f"📌 Model: {settings.groq_model if settings.llm_mode == 'groq' else settings.ollama_model}")
    print(f"📌 Headless: {settings.headless_mode}")
    print(f"📌 Vision: {settings.browser_use_vision}")
    print(f"📌 Google Search: {settings.google_search_enabled}")
    print(f"📌 Max URLs/search: {settings.max_urls_per_search}")
    print(f"📌 Delay between URLs: {settings.delay_between_urls}s")
    print("=" * 60)

    # Initialize agent
    print("\n🔧 Initializing agent...")
    agent = RealEstateSearchAgent()

    # Health check
    print("\n🏥 Health check...")
    health = await agent.health_check()
    print(f"   Status: {health['status']}")
    if health['status'] == 'healthy':
        print(f"   LLM: {health['llm_class']}")
        print(f"   Response time: {health['response_time_ms']}ms")
    else:
        print(f"   Error: {health.get('error', 'Unknown')}")
        print("❌ LLM not healthy, exiting...")
        sys.exit(1)

    # Test query
    query = "Tìm căn hộ 2 phòng ngủ quận Cầu Giấy Hà Nội giá 2-3 tỷ"
    print(f"\n📝 Query: {query}")

    try:
        # Execute search
        result = await agent.search(query=query, max_results=15)

        print(f"\n{'='*60}")
        print(f"📊 FINAL RESULTS SUMMARY")
        print(f"{'='*60}")
        print(f"✅ Total listings: {result.total_found}")
        print(f"⏱️  Duration: {result.execution_time_ms / 1000:.2f}s")
        print(f"🌐 Sources: {', '.join(set(result.sources_searched))}")

        if result.errors:
            print(f"⚠️  Errors: {len(result.errors)}")
            for err in result.errors[:3]:
                print(f"   - {err[:80]}")

        # Display sample results
        if result.listings:
            print(f"\n📋 Sample Listings (showing {min(5, len(result.listings))} of {len(result.listings)}):")

            for i, listing in enumerate(result.listings[:5], 1):
                title = listing.get('title', 'N/A')
                price = listing.get('price_text', 'N/A')
                location = listing.get('location', 'N/A')
                url = listing.get('url') or listing.get('source_url', 'N/A')
                platform = listing.get('source_platform', 'unknown')

                print(f"\n{i}. [{platform}] {title[:70]}...")
                print(f"   💰 Price: {price}")
                print(f"   📍 Location: {location}")
                print(f"   🔗 URL: {str(url)[:65]}...")

            # Save results to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"search_results_{timestamp}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump({
                    "query": query,
                    "total_found": result.total_found,
                    "sources": list(set(result.sources_searched)),
                    "execution_time_ms": result.execution_time_ms,
                    "listings": result.listings
                }, f, indent=2, ensure_ascii=False)

            print(f"\n💾 Results saved to: {filename}")

        print("\n" + "=" * 60)
        print("✨ Test completed successfully!")
        return result

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_google_first_search())
