"""
FastAPI Main Application.
BDS Agent - Hệ thống tìm kiếm bất động sản tự động.
"""

import asyncio
import sys
import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

# Fix for Python 3.13 on Windows - Playwright compatibility
if sys.platform == 'win32' and sys.version_info >= (3, 13):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from api.routes import search, listings, analytics
from storage.database import init_db, close_db, get_session
from storage.vector_db import VectorDB
from scheduler.jobs import get_scheduler, setup_jobs
from config import settings

# Setup structured logging
try:
    from core.logging import setup_logging, get_logger, set_trace_id, reset_trace_id
    setup_logging()
    logger = get_logger(__name__)
except ImportError:
    import structlog
    logger = structlog.get_logger(__name__)
    def set_trace_id(x): pass
    def reset_trace_id(): return str(uuid.uuid4())[:8]


class TraceMiddleware(BaseHTTPMiddleware):
    """Middleware to add trace_id to all requests."""

    async def dispatch(self, request: Request, call_next):
        # Get or generate trace_id
        trace_id = request.headers.get("X-Trace-ID") or reset_trace_id()
        set_trace_id(trace_id)

        start_time = time.time()

        logger.info(
            "request_started",
            method=request.method,
            url=str(request.url.path),
            client=request.client.host if request.client else "unknown",
            trace_id=trace_id,
        )

        response = await call_next(request)

        latency_ms = (time.time() - start_time) * 1000

        logger.info(
            "request_completed",
            method=request.method,
            url=str(request.url.path),
            status_code=response.status_code,
            latency_ms=round(latency_ms, 2),
            trace_id=trace_id,
        )

        # Add trace_id to response headers
        response.headers["X-Trace-ID"] = trace_id

        return response


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan handler.
    Khởi tạo và cleanup resources.
    """
    logger.info("🚀 Starting BDS Agent API...")

    # Initialize database
    try:
        await init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.warning("⚠️ Database init skipped (tables may already exist)", error=str(e))

    # Initialize vector database (lazy - will init on first use)
    # Skip during startup to avoid blocking on model download
    app.state.vector_db = None
    logger.info("⏳ Vector database will initialize on first use")

    # Setup scheduler
    try:
        scheduler = get_scheduler()
        setup_jobs()
        scheduler.start()
        app.state.scheduler = scheduler
        logger.info("✅ Scheduler started")
    except Exception as e:
        logger.error("⚠️ Scheduler setup failed (continuing)", error=str(e))
        app.state.scheduler = None

    logger.info("🎉 BDS Agent API ready!")

    yield

    # Cleanup
    logger.info("🛑 Shutting down BDS Agent API...")

    if hasattr(app.state, "scheduler") and app.state.scheduler:
        app.state.scheduler.shutdown(wait=False)
        logger.info("✅ Scheduler stopped")

    await close_db()
    logger.info("✅ Database closed")

    logger.info("👋 Goodbye!")


# Create FastAPI app
app = FastAPI(
    title="BDS Agent API",
    description="""
## Hệ thống tìm kiếm và quản lý tin bất động sản tự động

### Tính năng:
- 🔍 **Tìm kiếm thông minh**: Agent AI tự động tìm kiếm trên nhiều nền tảng
- 📊 **Phân tích thị trường**: Thống kê giá theo quận/huyện
- 🎯 **Semantic Search**: Tìm kiếm ngữ nghĩa với ChromaDB
- 📱 **Real-time Updates**: WebSocket cho updates real-time
- 🔔 **Thông báo**: Telegram notifications cho tin mới

### Tech Stack:
- 🤖 Ollama (qwen2.5:14b) - LLM local
- 🌐 Browser-use - Web automation
- 🗃️ PostgreSQL + ChromaDB - Storage
- ⚡ FastAPI - Backend
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trace ID middleware
app.add_middleware(TraceMiddleware)


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(
        "unhandled_exception",
        error=str(exc),
        url=str(request.url),
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An error occurred",
        },
    )


# Include routers
app.include_router(search.router, prefix="/api/v1")
app.include_router(listings.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")


# Health check
@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    Kiểm tra trạng thái hệ thống.
    """
    health = {
        "status": "healthy",
        "services": {},
    }

    # Check database
    try:
        from sqlalchemy import text
        async with get_session() as session:
            await session.execute(text("SELECT 1"))
        health["services"]["database"] = "ok"
    except Exception as e:
        health["services"]["database"] = f"error: {str(e)}"
        health["status"] = "degraded"

    # Check vector db
    if hasattr(app.state, "vector_db") and app.state.vector_db:
        try:
            count = app.state.vector_db.collection.count()
            health["services"]["vector_db"] = f"ok ({count} vectors)"
        except Exception as e:
            health["services"]["vector_db"] = f"error: {str(e)}"
    else:
        health["services"]["vector_db"] = "not initialized"

    # Check scheduler
    if hasattr(app.state, "scheduler") and app.state.scheduler:
        try:
            jobs = app.state.scheduler.get_jobs()
            health["services"]["scheduler"] = f"ok ({len(jobs)} jobs)"
        except Exception as e:
            health["services"]["scheduler"] = f"error: {str(e)}"
    else:
        health["services"]["scheduler"] = "not initialized"

    return health


@app.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint.
    Returns 200 only if database is connected and ready to serve traffic.
    """
    # Check database connectivity
    try:
        from sqlalchemy import text
        async with get_session() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "not ready", "database": f"error: {str(e)}"}
        )


@app.get("/api/v1/platforms")
async def get_platforms():
    """
    Get status of all crawler platforms.

    Returns list of supported real estate platforms with their status.
    """
    try:
        from crawlers.adapters import PlatformRegistry
        platforms = PlatformRegistry.list_platforms()
        stats = PlatformRegistry.get_stats()
        available = PlatformRegistry.get_available()

        return {
            "platforms": platforms,
            "stats": stats,
            "total_count": len(platforms),
            "available_count": len(available),
        }
    except Exception as e:
        logger.error("Failed to get platforms", error=str(e))
        return {"platforms": [], "total_count": 0, "available_count": 0, "error": str(e)}


@app.get("/api/v1/search/multi")
async def multi_platform_search(
    q: str = "",
    city: str = None,
    district: str = None,
    min_price: float = None,
    max_price: float = None,
    min_area: float = None,
    max_area: float = None,
    page: int = 1,
):
    """
    Search across all real estate platforms simultaneously.

    This endpoint uses the orchestrator to:
    - Fan out requests to all 10+ platforms in parallel
    - Handle rate limiting and graceful degradation
    - Aggregate and deduplicate results

    Args:
        q: Search query (e.g., "nhà phố")
        city: City filter (e.g., "Hanoi", "HCM")
        district: District filter
        min_price: Minimum price in VND
        max_price: Maximum price in VND
        min_area: Minimum area in m²
        max_area: Maximum area in m²
        page: Page number

    Returns:
        Aggregated search results with platform status
    """
    try:
        from crawlers.orchestrator import search_all_platforms

        logger.info(
            "multi_platform_search",
            query=q,
            city=city,
            page=page,
        )

        results = await search_all_platforms(
            query=q,
            city=city,
            district=district,
            min_price=min_price,
            max_price=max_price,
            min_area=min_area,
            max_area=max_area,
            page=page,
        )

        return results.to_dict()

    except Exception as e:
        logger.error("Multi-platform search failed", error=str(e))
        return JSONResponse(
            status_code=500,
            content={
                "error": "Search failed",
                "message": str(e) if settings.DEBUG else "An error occurred during search",
            },
        )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "BDS Agent API",
        "version": "1.0.0",
        "description": "Hệ thống tìm kiếm bất động sản tự động",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/api/v1/districts")
async def get_districts():
    """
    Lấy danh sách quận/huyện và giá tham khảo.
    """
    from config import DISTRICT_PRICE_RANGES

    districts = []
    for name, (min_price, max_price) in DISTRICT_PRICE_RANGES.items():
        districts.append({
            "name": name,
            "price_range_per_m2": {
                "min": min_price * 1_000_000,
                "max": max_price * 1_000_000,
                "display": f"{min_price}-{max_price} triệu/m²",
            },
        })

    return {"districts": districts}


@app.get("/api/v1/property-types")
async def get_property_types():
    """
    Lấy danh sách loại BĐS.
    """
    from config import PROPERTY_TYPES

    return {"property_types": PROPERTY_TYPES}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
