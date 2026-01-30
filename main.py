"""
BDS Agent - Real Estate Search & Management System
Main entry point - Crawl4AI Version
"""
import asyncio
import sys
import json
from datetime import datetime

from loguru import logger

from config import settings
from services.search_service import RealEstateSearchService
from api.routes.search import quick_search


def setup_logging():
    """Configure logging with loguru."""
    # Remove default handler
    logger.remove()

    # Add console handler with color
    logger.add(
        sys.stdout,
        level=settings.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
               "<level>{message}</level>",
        colorize=True,
    )

    # Add file handler for errors
    logger.add(
        "logs/error.log",
        level="ERROR",
        rotation="10 MB",
        retention="7 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
    )

    # Add file handler for all logs
    logger.add(
        "logs/bds_agent.log",
        level="DEBUG",
        rotation="50 MB",
        retention="7 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
    )


async def demo_search():
    """Demo search functionality with Crawl4AI."""
    print("\n" + "=" * 60)
    print("🏠 BDS Agent - Crawl4AI Demo")
    print("=" * 60 + "\n")

    # Example queries
    demo_queries = [
        "Tìm chung cư 2PN Cầu Giấy 2-3 tỷ",
        "Nhà riêng Ba Đình dưới 5 tỷ",
        "Đất nền Hà Đông 1-2 tỷ",
    ]

    print("Các query demo:")
    for i, q in enumerate(demo_queries, 1):
        print(f"  {i}. {q}")

    print("\nNhập số (1-3) để chọn query, hoặc nhập query của bạn:")
    user_input = input("> ").strip()

    if user_input.isdigit() and 1 <= int(user_input) <= len(demo_queries):
        query = demo_queries[int(user_input) - 1]
    else:
        query = user_input if user_input else demo_queries[0]

    print(f"\n🔍 Đang tìm kiếm: {query}\n")

    service = RealEstateSearchService()

    try:
        # Search with Crawl4AI
        results = await service.search(
            query,
            max_results=30
        )

        print("\n" + "-" * 60)
        print(f"📊 KẾT QUẢ TÌM KIẾM")
        print("-" * 60)
        print(f"  Tổng số kết quả: {len(results)}")

        # Show sample results
        if results:
            print(f"\n📋 Mẫu kết quả:")
            for i, listing in enumerate(results[:5], 1):
                print(f"\n  {i}. {listing['title'][:80]}")
                print(f"     💰 {listing['price_text']}")
                print(f"     📍 {listing['location']['address'][:60]}")
                print(f"     🌐 {listing['source_platform']}")

            # Save to JSON
            with open("search_results.json", "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)
            print(f"\n  💾 Đã lưu vào search_results.json")
        else:
            print("\n  ❌ Không tìm thấy kết quả nào")

    except Exception as e:
        logger.error(f"Search error: {e}")
        print(f"\n❌ Lỗi: {e}")
async def interactive_mode():
    """Interactive search mode."""
    print("\n" + "=" * 60)
    print("🏠 BDS Agent - Chế độ tương tác")
    print("=" * 60)
    print("\nNhập 'exit' để thoát, 'help' để xem hướng dẫn\n")

    service = RealEstateSearchService()

    while True:
        query = input("\n🔍 Nhập query: ").strip()

        if not query:
            continue

        if query.lower() == 'exit':
            print("👋 Tạm biệt!")
            break

        if query.lower() == 'help':
            print("""
Hướng dẫn sử dụng:
- Nhập query tự nhiên: "chung cư 2PN Cầu Giấy 2-3 tỷ"
- Có thể chỉ định: loại BĐS, khu vực, giá, số phòng
- Ví dụ:
  + "Tìm nhà riêng Ba Đình dưới 5 tỷ"
  + "Đất nền Hà Đông 1-2 tỷ"
  + "Chung cư 3PN Tây Hồ view hồ"
            """)
            continue

        print(f"\n⏳ Đang tìm kiếm...")

        try:
            results = await service.search(query, max_results=10)

            print(f"\n📊 Kết quả: {len(results)} listings")

            for i, listing in enumerate(results[:5], 1):
                print(f"\n  [{i}] {listing['title'][:50]}...")
                print(f"      Giá: {listing.get('price_text', 'N/A')} | "
                      f"DT: {listing.get('area_m2', 'N/A')}m²")
        except Exception as e:
            print(f"❌ Lỗi: {e}")


async def main():
    """Main entry point."""
    setup_logging()

    logger.info("Starting BDS Agent...")
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"Ollama model: {settings.ollama_model}")

    # Check command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "demo":
            await demo_search()

        elif command == "interactive":
            await interactive_mode()

        elif command == "search":
            if len(sys.argv) > 2:
                query = " ".join(sys.argv[2:])
                result = await quick_search(query)
                print(f"Found {result.total_found} results")
                for listing in result.listings:
                    print(f"  - {listing['title']}")
            else:
                print("Usage: python main.py search <query>")

        elif command == "api":
            # Start FastAPI server
            import uvicorn
            from api.main import app

            uvicorn.run(
                app,
                host=settings.api_host,
                port=settings.api_port,
                reload=settings.api_reload,
            )

        elif command == "scheduler":
            # Start scheduler only
            from scheduler.jobs import start_scheduler
            await start_scheduler()

        else:
            print(f"""
BDS Agent - Real Estate Search System

Usage:
  python main.py <command>

Commands:
  demo         - Chạy demo search với UI console
  interactive  - Chế độ tương tác liên tục
  search <q>   - Tìm kiếm nhanh với query
  api          - Khởi động FastAPI server
  scheduler    - Khởi động background scheduler

Examples:
  python main.py demo
  python main.py search "chung cư 2PN Cầu Giấy 2-3 tỷ"
  python main.py api
            """)
    else:
        # Default: run demo
        await demo_search()


if __name__ == "__main__":
    asyncio.run(main())
