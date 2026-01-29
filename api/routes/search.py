"""
Search API Routes.
Implements the main search endpoint with real-time and cached modes.
"""

from datetime import datetime
from typing import Optional, AsyncGenerator
import json

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import StreamingResponse
from loguru import logger

from api.models import (
    SearchRequest,
    SearchResponse,
    SearchResultItem,
    LocationSchema,
    ContactSchema,
    ErrorResponse,
)
from services.search_service import RealEstateSearchService
from storage.vector_db import semantic_search, get_vector_db
from storage.database import get_session, ListingCRUD
from services.validator import get_validator


router = APIRouter(prefix="/search", tags=["Search"])


# Active WebSocket connections for search progress
active_connections: dict[str, WebSocket] = {}


def listing_to_search_result(listing: dict) -> SearchResultItem:
    """Convert listing dict to SearchResultItem."""
    location = listing.get("location", {})
    if isinstance(location, dict):
        location_schema = LocationSchema(
            address=location.get("address"),
            ward=location.get("ward"),
            district=location.get("district"),
            city=location.get("city", "Hà Nội"),
        )
    else:
        location_schema = None

    contact = listing.get("contact", {})
    if isinstance(contact, dict):
        contact_schema = ContactSchema(
            name=contact.get("name"),
            phone=contact.get("phone"),
            phone_clean=contact.get("phone_clean"),
            phones=contact.get("phones", []),
            zalo=contact.get("zalo", []),
            facebook=contact.get("facebook", []),
            email=contact.get("email", []),
        )
    else:
        contact_schema = None

    return SearchResultItem(
        id=listing.get("id", ""),
        title=listing.get("title", ""),
        price_text=listing.get("price_text"),
        price_number=listing.get("price_number"),
        area_m2=listing.get("area_m2"),
        location=location_schema,
        contact=contact_schema,
        thumbnail=listing.get("thumbnail") or (listing.get("images", [None])[0] if listing.get("images") else None),
        source_url=listing.get("source_url", ""),
        source_platform=listing.get("source_platform", ""),
        property_type=listing.get("property_type"),
        bedrooms=listing.get("bedrooms"),
        similarity_score=listing.get("similarity_score"),
    )


@router.post("", response_model=SearchResponse)
async def search_listings(request: SearchRequest) -> SearchResponse:
    """
    Search for real estate listings.

    - First searches vector DB for cached results
    - If insufficient results and search_realtime=True, performs real-time scraping
    """
    start_time = datetime.now()

    logger.info(f"Search request: query='{request.query}', realtime={request.search_realtime}")

    results = []
    sources = []
    errors = []
    from_cache = True
    synthesis = None

    try:
        # Build filters for vector search
        filters = {}
        if request.filters:
            if request.filters.property_type:
                filters["property_type"] = request.filters.property_type
            if request.filters.district:
                filters["district"] = request.filters.district
            if request.filters.min_price:
                filters["price_min"] = request.filters.min_price
            if request.filters.max_price:
                filters["price_max"] = request.filters.max_price
            if request.filters.bedrooms:
                filters["bedrooms"] = request.filters.bedrooms
            if request.filters.source_platform:
                filters["source_platform"] = request.filters.source_platform

        # Step 1: Search vector DB
        vector_results = await semantic_search(
            request.query,
            n_results=request.max_results,
            filters=filters if filters else None,
        )

        if vector_results:
            sources.append("vector_db")
            for r in vector_results:
                results.append(listing_to_search_result(r))

        # Step 2: If not enough results and real-time requested, scrape
        if len(results) < 10 and request.search_realtime:
            from_cache = False

            service = RealEstateSearchService()
            try:
                search_results = await service.search(
                    request.query,
                    max_results=request.max_results
                )

                sources.append("crawl4ai_realtime")

                # Add real-time results
                for listing in search_results:
                    results.append(listing_to_search_result(listing))

                logger.info(f"Real-time search returned {len(search_results)} listings")

            except Exception as e:
                logger.error(f"Real-time search error: {e}")
                errors.append(str(e))

        # Deduplicate by ID
        seen_ids = set()
        unique_results = []
        for r in results:
            if r.id not in seen_ids:
                seen_ids.add(r.id)
                unique_results.append(r)

        results = unique_results[:request.max_results]

    except Exception as e:
        logger.error(f"Search error: {e}")
        errors.append(str(e))

    execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

    return SearchResponse(
        results=results,
        total=len(results),
        from_cache=from_cache,
        sources=list(set(sources)),
        execution_time_ms=execution_time,
        synthesis=synthesis,
        errors=errors,
    )


@router.post("/stream")
async def search_stream(request: SearchRequest):
    """
    Streaming search endpoint - returns results progressively as they are found.
    Uses Server-Sent Events (SSE) format.
    """

    async def generate_stream() -> AsyncGenerator[str, None]:
        """Generate SSE stream of search results"""

        service = RealEstateSearchService()

        try:
            async for message in service.search_stream(
                user_query=request.query,
                max_results=request.max_results or 50
            ):
                # Convert to SSE format
                yield f"data: {json.dumps(message, default=str, ensure_ascii=False)}\n\n"

        except Exception as e:
            logger.error(f"Streaming search error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/quick")
async def quick_search(
    q: str,
    limit: int = 10,
    district: Optional[str] = None,
    property_type: Optional[str] = None,
) -> SearchResponse:
    """
    Quick search endpoint for autocomplete/suggestions.
    Only searches cached data, no real-time scraping.
    """
    start_time = datetime.now()

    filters = {}
    if district:
        filters["district"] = district
    if property_type:
        filters["property_type"] = property_type

    vector_results = await semantic_search(
        q,
        n_results=limit,
        filters=filters if filters else None,
    )

    results = [listing_to_search_result(r) for r in vector_results]

    execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

    return SearchResponse(
        results=results,
        total=len(results),
        from_cache=True,
        sources=["vector_db"],
        execution_time_ms=execution_time,
    )


@router.websocket("/ws")
async def websocket_search(websocket: WebSocket):
    """
    WebSocket endpoint for real-time search with progress updates.

    Send: {"query": "...", "filters": {...}}
    Receive: progress updates and final results
    """
    await websocket.accept()

    try:
        while True:
            # Receive search request
            data = await websocket.receive_json()
            query = data.get("query")

            if not query:
                await websocket.send_json({
                    "type": "error",
                    "error": "Query is required",
                })
                continue

            logger.info(f"WebSocket search: {query}")

            # Progress callback
            async def send_progress(update: dict):
                await websocket.send_json({
                    "type": "progress",
                    **update,
                })

            # Perform search with progress
            agent = RealEstateSearchAgent(headless=True)

            try:
                result = await agent.search_with_progress(
                    query,
                    progress_callback=send_progress,
                    max_results=data.get("max_results", 20),
                    platforms=data.get("platforms"),
                )

                # Send final result
                await websocket.send_json({
                    "type": "result",
                    "data": {
                        "results": [
                            listing_to_search_result(l).model_dump()
                            for l in result.listings
                        ],
                        "total": result.total_found,
                        "sources": result.sources_searched,
                        "errors": result.errors,
                    },
                })

            finally:
                await agent.close()

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "error": str(e),
            })
        except:
            pass


@router.get("/stats")
async def get_search_stats():
    """Get search/vector DB statistics."""
    db = get_vector_db()
    stats = await db.get_stats()
    return stats
