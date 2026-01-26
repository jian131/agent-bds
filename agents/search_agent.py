"""
Core Real Estate Search Agent using browser-use with Groq API.
Implements Google-First search strategy with multi-platform scraping.
Supports Groq API (fast) with Ollama fallback (local).
"""
import asyncio
import json
import re
import time
from collections import deque
from datetime import datetime, timedelta
from typing import Any, Optional, List, Dict
from dataclasses import dataclass, field

from browser_use import Agent, Browser
from loguru import logger

from config import settings


# Platform priorities for scraping
PLATFORM_PRIORITY = {
    'batdongsan': 1,
    'chotot': 1,
    'mogi': 2,
    'alonhadat': 2,
    'nhadat247': 2,
    'muaban': 3,
    'facebook': 3,
    'other': 4
}


@dataclass
class SearchIntent:
    """Parsed search intent from user query."""
    property_type: Optional[str] = None
    city: str = "Hà Nội"
    district: Optional[str] = None
    ward: Optional[str] = None
    street: Optional[str] = None
    price_min: Optional[int] = None
    price_max: Optional[int] = None
    price_text: Optional[str] = None
    area_min: Optional[float] = None
    area_max: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    features: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    intent: str = "mua"  # mua or thuê

    @classmethod
    def from_dict(cls, data: dict) -> "SearchIntent":
        """Create SearchIntent from parsed dict."""
        location = data.get("location", {})
        price = data.get("price", {})
        area = data.get("area", {})

        return cls(
            property_type=data.get("property_type"),
            city=location.get("city", "Hà Nội"),
            district=location.get("district"),
            ward=location.get("ward"),
            street=location.get("street"),
            price_min=price.get("min"),
            price_max=price.get("max"),
            price_text=price.get("text"),
            area_min=area.get("min"),
            area_max=area.get("max"),
            bedrooms=data.get("bedrooms"),
            bathrooms=data.get("bathrooms"),
            features=data.get("features", []),
            keywords=data.get("keywords", []),
            intent=data.get("intent", "mua"),
        )

    def to_search_query(self) -> str:
        """Convert intent to natural language search query."""
        parts = []

        if self.intent == "thuê":
            parts.append("cho thuê")
        else:
            parts.append("mua bán")

        if self.property_type:
            parts.append(self.property_type)

        if self.bedrooms:
            parts.append(f"{self.bedrooms} phòng ngủ")

        if self.district:
            parts.append(self.district)

        if self.city and self.city != "Hà Nội":
            parts.append(self.city)

        if self.price_text:
            parts.append(self.price_text)
        elif self.price_min and self.price_max:
            min_text = f"{self.price_min / 1_000_000_000:.1f} tỷ"
            max_text = f"{self.price_max / 1_000_000_000:.1f} tỷ"
            parts.append(f"{min_text} - {max_text}")

        return " ".join(parts)


@dataclass
class SearchResult:
    """Result from a search operation."""
    listings: list[dict] = field(default_factory=list)
    total_found: int = 0
    sources_searched: list[str] = field(default_factory=list)
    from_cache: bool = False
    execution_time_ms: int = 0
    errors: list[str] = field(default_factory=list)
    synthesis: Optional[str] = None


class RealEstateSearchAgent:
    """
    AI Agent for searching and scraping real estate listings.
    Uses Google-first strategy to discover URLs, then scrapes multiple platforms.
    Supports Groq API (fast, free) with Ollama fallback (local).
    """

    def __init__(self):
        """Initialize the search agent with LLM and rate limiter."""
        self.llm = self._init_llm()
        self.llm_type = "groq" if "Groq" in type(self.llm).__name__ else "ollama"

        # Rate limiter for Groq API
        self.request_times = deque(maxlen=30)
        self.rate_limit_per_minute = settings.rate_limit_per_minute

        logger.info(f"✅ Agent initialized with LLM: {type(self.llm).__name__}")
        logger.info(f"✅ Browser headless: {settings.headless_mode}")
        logger.info(f"✅ Vision mode: {settings.browser_use_vision}")
        logger.info(f"✅ Google-first search: {settings.google_search_enabled}")

    def _init_llm(self):
        """Initialize LLM with Groq → Ollama fallback strategy."""

        # Try Groq first (if configured) - using browser-use native ChatGroq
        if settings.llm_mode == "groq" and settings.groq_api_key:
            try:
                from browser_use.llm.groq.chat import ChatGroq as BrowserUseGroq

                llm = BrowserUseGroq(
                    model=settings.groq_model,
                    api_key=settings.groq_api_key,
                    temperature=0.1,
                    timeout=30,
                    max_retries=2
                )

                logger.info(f"✅ Using browser-use Groq: {settings.groq_model}")
                logger.warning("⚠️ Note: Groq free tier has 500k tokens/day limit")
                return llm

            except Exception as e:
                logger.warning(f"⚠️ Groq failed: {e}")
                logger.info("⚠️ Falling back to Gemini or Ollama...")

        # Try Gemini (if configured) - FREE 15 RPM, 1500 RPD
        if settings.llm_mode == "gemini" and settings.gemini_api_key:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI

                llm = ChatGoogleGenerativeAI(
                    model=settings.gemini_model,
                    google_api_key=settings.gemini_api_key,
                    temperature=0.1,
                    max_retries=2,
                    timeout=60,
                )

                logger.info(f"✅ Using Gemini: {settings.gemini_model}")
                logger.info("💡 Gemini FREE tier: 15 RPM, 1500 requests/day")
                return llm

            except Exception as e:
                logger.warning(f"⚠️ Gemini failed: {e}")
                logger.info("⚠️ Falling back to Ollama local...")

        # Fallback to Ollama local - using browser-use native ChatOllama
        try:
            from browser_use.llm.ollama.chat import ChatOllama as BrowserUseOllama

            llm = BrowserUseOllama(
                model=settings.ollama_model,
                host=settings.ollama_base_url,
            )
            logger.info(f"✅ Using browser-use Ollama: {settings.ollama_model}")
            return llm
        except Exception as e:
            logger.error(f"❌ Failed to initialize any LLM: {e}")
            raise RuntimeError("No LLM available. Check Groq API key or Ollama installation.")

    async def parse_query(self, query: str) -> SearchIntent:
        """Parse natural language query into structured search intent."""
        logger.info(f"Parsing query: {query}")

        prompt = f"""Phân tích query tìm kiếm bất động sản và trả về JSON:

Query: {query}

Trả về CHÍNH XÁC JSON format (không có text khác):
{{
    "property_type": "chung cư | nhà riêng | biệt thự | đất nền | null",
    "location": {{
        "city": "Hà Nội | Hồ Chí Minh",
        "district": "tên quận/huyện hoặc null"
    }},
    "price": {{
        "min": số_tiền_VND_hoặc_null,
        "max": số_tiền_VND_hoặc_null,
        "text": "text giá như 2-3 tỷ"
    }},
    "bedrooms": số_hoặc_null,
    "intent": "mua | thuê"
}}

Lưu ý: 1 tỷ = 1000000000, 1 triệu = 1000000
"""

        try:
            # Different message format for different LLMs
            if "Gemini" in type(self.llm).__name__ or "Google" in type(self.llm).__name__:
                from langchain_core.messages import HumanMessage
                response = await self.llm.ainvoke([HumanMessage(content=prompt)])
                content = response.content if hasattr(response, 'content') else str(response)
            else:
                from browser_use.llm import UserMessage
                response = await self.llm.ainvoke([UserMessage(content=prompt)])
                content = response.completion if hasattr(response, 'completion') else str(response)

            # Extract JSON safely
            parsed = self._safe_parse_json(content)
            if parsed:
                intent = SearchIntent.from_dict(parsed)
                logger.info(f"Parsed intent: property_type={intent.property_type}, "
                           f"district={intent.district}, price={intent.price_text}")
                return intent

        except Exception as e:
            logger.warning(f"Query parsing error: {e}")

        # Fallback: basic regex parsing
        return self._fallback_parse_query(query)

    def _safe_parse_json(self, text: str) -> Optional[dict]:
        """Safely extract and parse JSON from text."""
        if not text:
            return None

        try:
            # Try direct parse
            return json.loads(text.strip())
        except:
            pass

        # Try to find JSON in text
        patterns = [
            r'```json\s*(.*?)\s*```',  # Markdown code block
            r'```\s*(.*?)\s*```',       # Generic code block
            r'\{[^{}]*\}',              # Simple JSON object
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    json_str = match.group(1) if '```' in pattern else match.group(0)
                    return json.loads(json_str.strip())
                except:
                    continue

        return None

    def _fallback_parse_query(self, query: str) -> SearchIntent:
        """Fallback query parsing using regex."""
        intent = SearchIntent()
        query_lower = query.lower()

        # Property type
        for ptype in ["chung cư", "căn hộ", "nhà riêng", "biệt thự", "đất nền", "nhà mặt phố"]:
            if ptype in query_lower:
                intent.property_type = ptype
                break

        # District detection
        districts = ["cầu giấy", "ba đình", "hoàn kiếm", "đống đa", "hai bà trưng",
                    "thanh xuân", "hoàng mai", "long biên", "nam từ liêm", "bắc từ liêm",
                    "tây hồ", "hà đông", "quận 1", "quận 2", "quận 3", "quận 7", "bình thạnh"]
        for district in districts:
            if district in query_lower:
                intent.district = district.title()
                break

        # Bedrooms
        bedroom_match = re.search(r'(\d+)\s*(pn|phòng ngủ|phong ngu|pn)', query_lower)
        if bedroom_match:
            intent.bedrooms = int(bedroom_match.group(1))

        # Price
        price_match = re.search(r'(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*tỷ', query_lower)
        if price_match:
            intent.price_min = int(float(price_match.group(1)) * 1_000_000_000)
            intent.price_max = int(float(price_match.group(2)) * 1_000_000_000)
            intent.price_text = f"{price_match.group(1)}-{price_match.group(2)} tỷ"
        else:
            # Check for "dưới X tỷ" or "under X billion"
            under_match = re.search(r'dưới\s*(\d+(?:\.\d+)?)\s*tỷ', query_lower)
            if under_match:
                intent.price_max = int(float(under_match.group(1)) * 1_000_000_000)
                intent.price_text = f"dưới {under_match.group(1)} tỷ"

        # City
        if "hồ chí minh" in query_lower or "sài gòn" in query_lower or "hcm" in query_lower:
            intent.city = "Hồ Chí Minh"

        # Intent (buy/rent)
        if "thuê" in query_lower or "cho thuê" in query_lower:
            intent.intent = "thuê"

        intent.keywords = [query]
        return intent

    async def search(self, query: str, max_results: int = 20) -> SearchResult:
        """
        MAIN SEARCH METHOD - Google-First Strategy

        Flow:
        1. Google search → discover URLs from multiple platforms
        2. Scrape each URL sequentially
        3. Aggregate + deduplicate
        4. Return all listings

        Args:
            query: Natural language search query
            max_results: Maximum results to return

        Returns:
            SearchResult with listings from multiple sources
        """
        start_time = datetime.now()
        result = SearchResult()

        print(f"\n{'='*60}")
        print(f"🏠 REAL ESTATE SEARCH: {query}")
        print(f"{'='*60}")

        try:
            # Parse query for intent understanding
            intent = await self.parse_query(query)

            all_listings = []

            if settings.google_search_enabled:
                # STEP 1: Google Search to discover URLs
                print("\n📍 STEP 1: Google Search for URLs")
                urls_to_scrape = await self._google_search_first(query, intent)

                if urls_to_scrape:
                    # STEP 2: Scrape each URL sequentially
                    print(f"\n📍 STEP 2: Scraping {len(urls_to_scrape)} URLs")

                    for i, url_data in enumerate(urls_to_scrape):
                        print(f"\n--- URL {i+1}/{len(urls_to_scrape)} ---")

                        # Rate limit check
                        await self._rate_limit_wait()

                        listings = await self._scrape_single_url(url_data)
                        if listings:
                            all_listings.extend(listings)
                            result.sources_searched.append(url_data.get('platform', 'unknown'))

                        # Delay between URLs for rate limit safety
                        if i < len(urls_to_scrape) - 1:
                            delay = settings.delay_between_urls
                            print(f"  ⏳ Cooling down {delay}s...")
                            await asyncio.sleep(delay)
                else:
                    print("⚠️ No URLs found from Google, falling back to direct scrape")
                    all_listings = await self._fallback_direct_scrape(intent, result)
            else:
                # Direct scrape without Google search
                all_listings = await self._fallback_direct_scrape(intent, result)

            # STEP 3: Deduplicate
            print(f"\n📍 STEP 3: Deduplication")
            result.listings = self._deduplicate_listings(all_listings)[:max_results]
            result.total_found = len(result.listings)

            print(f"\n{'='*60}")
            print(f"✅ TOTAL: {result.total_found} unique listings")
            print(f"   (from {len(all_listings)} raw results)")
            print(f"   Sources: {', '.join(set(result.sources_searched))}")
            print(f"{'='*60}")

        except Exception as e:
            logger.error(f"Search error: {e}")
            result.errors.append(str(e))
            import traceback
            traceback.print_exc()

        result.execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        logger.info(f"Search completed: {result.total_found} results in {result.execution_time_ms}ms")

        return result

    async def _google_search_first(self, user_query: str, intent: SearchIntent) -> List[Dict]:
        """
        Step 1: Google search để tìm URLs phù hợp từ nhiều platforms.

        Returns:
            List of URL data dicts to scrape
        """
        print("\n🔍 Google Search for real estate URLs...")

        # Build optimized Google search query
        search_query = self._build_google_query(user_query, intent)
        print(f"   Search query: {search_query}")

        task = f"""
NHIỆM VỤ: Google search và collect URLs bất động sản

1. Navigate to https://www.google.com
2. Search: "{search_query}"
3. Wait for results to load
4. Extract TOP 10-12 organic results (skip ads):
   - URL của mỗi kết quả
   - Title snippet

5. Identify platform từ URL:
   - chotot.com hoặc nhatot.com → "chotot"
   - batdongsan.com.vn → "batdongsan"
   - mogi.vn → "mogi"
   - alonhadat.com.vn → "alonhadat"
   - nhadat247.com.vn → "nhadat247"
   - muaban.net → "muaban"
   - facebook.com → "facebook"
   - other → "other"

6. LOẠI BỎ URLs từ:
   - Tin tức: vnexpress, dantri, cafef, vietnamnet
   - Ads/sponsored links
   - Youtube, tiktok
   - Diễn đàn: webtretho, otofun

7. Return JSON array:
[
  {{"url": "https://...", "platform": "batdongsan", "title": "..."}},
  {{"url": "https://...", "platform": "chotot", "title": "..."}}
]

CHỈ return JSON array, không có text khác.
"""

        try:
            agent = Agent(
                task=task,
                llm=self.llm,
                use_vision=settings.browser_use_vision,
                max_actions_per_step=3,
            )

            result = await agent.run(max_steps=settings.max_steps_google_search)
            urls_data = self._parse_google_results(result)

            if urls_data:
                # Sort by platform priority
                urls_data.sort(key=lambda x: PLATFORM_PRIORITY.get(x.get('platform', 'other'), 4))

                # Limit to max URLs
                urls_data = urls_data[:settings.max_urls_per_search]

                print(f"   ✅ Found {len(urls_data)} relevant URLs:")
                for u in urls_data:
                    print(f"      - [{u.get('platform')}] {u.get('url', '')[:60]}...")

                return urls_data
            else:
                print("   ⚠️ No URLs parsed from Google results")
                return []

        except Exception as e:
            logger.error(f"Google search error: {e}")
            print(f"   ❌ Google search error: {e}")
            return []

    def _build_google_query(self, user_query: str, intent: SearchIntent) -> str:
        """Build optimized Google search query."""
        parts = []

        # Intent
        if intent.intent == "thuê":
            parts.append("cho thuê")
        else:
            parts.append("mua bán")

        # Property type
        if intent.property_type:
            parts.append(intent.property_type)

        # Bedrooms
        if intent.bedrooms:
            parts.append(f"{intent.bedrooms} phòng ngủ")

        # Location
        if intent.district:
            parts.append(intent.district)
        parts.append(intent.city or "Hà Nội")

        # Price
        if intent.price_text:
            parts.append(intent.price_text)

        return " ".join(parts)

    def _parse_google_results(self, result: Any) -> List[Dict]:
        """Parse Google search agent results into URL list."""
        try:
            content = None

            # Handle AgentHistoryList
            if hasattr(result, 'final_result'):
                content = result.final_result()
            elif hasattr(result, 'last_result'):
                content = result.last_result()
            else:
                content = str(result)

            # Already a list
            if isinstance(content, list):
                return self._validate_urls(content)

            # Parse string
            if isinstance(content, str):
                parsed = self._safe_parse_json(content)
                if isinstance(parsed, list):
                    return self._validate_urls(parsed)

                # Try to find JSON array in text
                match = re.search(r'\[.*\]', content, re.DOTALL)
                if match:
                    try:
                        urls = json.loads(match.group(0))
                        return self._validate_urls(urls)
                    except:
                        pass

            # Dict format
            if isinstance(content, dict):
                for key in ['urls', 'results', 'data']:
                    if key in content and isinstance(content[key], list):
                        return self._validate_urls(content[key])

        except Exception as e:
            logger.warning(f"Parse Google results error: {e}")

        return []

    def _validate_urls(self, urls: List[Dict]) -> List[Dict]:
        """Validate and clean URL list."""
        valid_urls = []
        seen = set()

        for item in urls:
            if not isinstance(item, dict):
                continue

            url = item.get('url', '')
            if not url or not url.startswith('http'):
                continue

            # Skip duplicates
            if url in seen:
                continue
            seen.add(url)

            # Auto-detect platform if not provided
            if not item.get('platform'):
                item['platform'] = self._detect_platform(url)

            # Skip unwanted platforms
            if item['platform'] in ['news', 'forum', 'video']:
                continue

            valid_urls.append(item)

        return valid_urls

    async def _scrape_single_url(self, url_data: Dict) -> List[Dict]:
        """
        Scrape listings từ 1 URL cụ thể.

        Args:
            url_data: {url, platform, title}

        Returns:
            List of listings
        """
        url = url_data.get('url', '')
        platform = url_data.get('platform', 'other')

        print(f"   🌐 Scraping [{platform}]: {url[:70]}...")

        # Build platform-specific task
        task = self._build_scrape_task(url, platform)

        try:
            agent = Agent(
                task=task,
                llm=self.llm,
                use_vision=settings.browser_use_vision,
                max_actions_per_step=3,
            )

            result = await agent.run(max_steps=settings.max_steps_per_url)
            listings = self._parse_agent_result(result)

            # Add source info to each listing
            for listing in listings:
                listing['source_platform'] = platform
                listing['source_url'] = url

            if listings:
                print(f"      ✅ Extracted {len(listings)} listings")
            else:
                print(f"      ⚠️ No listings found")

            return listings

        except Exception as e:
            logger.error(f"Scrape error for {url}: {e}")
            print(f"      ❌ Scrape error: {e}")
            return []

    def _build_scrape_task(self, url: str, platform: str) -> str:
        """Build scraping task based on platform."""

        if platform == 'facebook':
            return f"""
NHIỆM VỤ: Extract BĐS posts từ Facebook

1. Navigate to: {url}
2. Wait for page to load
3. Scroll để load thêm content nếu cần
4. Extract posts/listings với:
   - title: tiêu đề hoặc dòng đầu post
   - price_text: giá (VD: "3.5 tỷ", "3500 triệu")
   - area_text: diện tích (VD: "85m2")
   - location: địa chỉ/khu vực
   - url: link post nếu có
   - contact: số điện thoại/zalo

5. Return JSON array (max 10 listings):
[{{"title": "...", "price_text": "...", "area_text": "...", "location": "...", "url": "...", "contact": "..."}}]

CHỈ return JSON array, không có text khác.
"""
        else:
            return f"""
NHIỆM VỤ: Extract BĐS listings từ {platform}

1. Navigate to: {url}
2. Wait for page to load completely
3. Xác định page type:
   - Nếu là SINGLE listing page: extract 1 listing đầy đủ
   - Nếu là LIST page: extract tất cả listings visible (max 10)

4. Với mỗi listing extract:
   - title: tiêu đề BĐS
   - price_text: giá hiển thị (VD: "3,5 tỷ", "35 triệu/tháng")
   - area_text: diện tích (VD: "85 m²")
   - location: địa chỉ đầy đủ hoặc quận/huyện
   - url: link chi tiết listing
   - bedrooms: số phòng ngủ (nếu có)
   - contact: số điện thoại (nếu hiển thị)

5. Return JSON array:
[{{"title": "...", "price_text": "...", "area_text": "...", "location": "...", "url": "...", "bedrooms": null, "contact": null}}]

CHỈ return JSON array với data THẬT từ page, không fake.
"""

    async def _fallback_direct_scrape(self, intent: SearchIntent, result: SearchResult) -> List[Dict]:
        """Fallback: scrape trực tiếp từ các trang chính."""
        print("\n📍 Fallback: Direct platform scrape")

        all_listings = []
        platforms = ["batdongsan", "chotot"]

        for platform in platforms:
            logger.info(f"Searching platform: {platform}")
            result.sources_searched.append(platform)

            try:
                await self._rate_limit_wait()
                res = await self._search_platform(platform, intent)
                if isinstance(res, list):
                    all_listings.extend(res)
                    logger.info(f"Platform {platform}: found {len(res)} listings")
            except Exception as e:
                logger.error(f"Platform {platform} error: {e}")
                result.errors.append(f"{platform}: {str(e)}")

            # Delay between platforms
            if platform != platforms[-1]:
                delay = settings.delay_between_urls
                logger.info(f"⏳ Waiting {delay}s for rate limit cooldown...")
                await asyncio.sleep(delay)

        return all_listings

    async def _rate_limit_wait(self):
        """Wait if approaching Groq rate limit."""
        now = time.time()
        self.request_times.append(now)

        # Check requests in last 60s
        one_minute_ago = now - 60
        recent_requests = [t for t in self.request_times if t > one_minute_ago]

        if len(recent_requests) >= self.rate_limit_per_minute:
            oldest = min(recent_requests)
            wait_time = 60 - (now - oldest) + 3  # +3s buffer

            if wait_time > 0:
                print(f"   ⏸️ Rate limit: waiting {wait_time:.0f}s...")
                await asyncio.sleep(wait_time)

    @staticmethod
    def _detect_platform(url: str) -> str:
        """Detect platform from URL."""
        url_lower = url.lower()

        if 'chotot.com' in url_lower or 'nhatot.com' in url_lower:
            return 'chotot'
        elif 'batdongsan.com' in url_lower:
            return 'batdongsan'
        elif 'facebook.com' in url_lower:
            return 'facebook'
        elif 'mogi.vn' in url_lower:
            return 'mogi'
        elif 'alonhadat.com' in url_lower:
            return 'alonhadat'
        elif 'nhadat247.com' in url_lower:
            return 'nhadat247'
        elif 'muaban.net' in url_lower:
            return 'muaban'
        elif any(x in url_lower for x in ['vnexpress', 'dantri', 'cafef', 'vietnamnet']):
            return 'news'
        elif any(x in url_lower for x in ['youtube', 'tiktok']):
            return 'video'
        elif any(x in url_lower for x in ['webtretho', 'otofun']):
            return 'forum'
        else:
            return 'other'

    async def _search_platform(self, platform: str, intent: SearchIntent) -> List[Dict]:
        """Search a specific platform."""
        if platform == "chotot":
            return await self._search_chotot(intent)
        elif platform == "batdongsan":
            return await self._search_batdongsan(intent)
        else:
            logger.warning(f"Platform {platform} not implemented")
            return []

    async def _search_chotot(self, intent: SearchIntent) -> List[Dict]:
        """Search Chợ Tốt for listings."""

        task = f"""
Tìm kiếm bất động sản trên Chợ Tốt:
- Loại: {intent.property_type or 'tất cả'}
- Khu vực: {intent.district or intent.city}
- Giá: {intent.price_text or 'không giới hạn'}
- Phòng ngủ: {intent.bedrooms or 'không giới hạn'}

Các bước:
1. Truy cập https://nha.chotot.com/ha-noi/mua-ban-bat-dong-san
2. Thu thập 5 listing đầu tiên
3. Cho mỗi listing, lấy: tiêu đề, giá, diện tích, địa chỉ, URL

Trả về JSON array:
[{{"title": "...", "price_text": "...", "area_text": "...", "location": "...", "url": "..."}}]
"""

        try:
            agent = Agent(
                task=task,
                llm=self.llm,
                use_vision=settings.browser_use_vision,
                max_actions_per_step=3,
            )

            result = await agent.run(max_steps=5)
            return self._parse_agent_result(result)

        except Exception as e:
            logger.error(f"Chợ Tốt search error: {e}")
            return []

    async def _search_batdongsan(self, intent: SearchIntent) -> List[Dict]:
        """Search Batdongsan.com.vn for listings."""

        # Build URL
        base_url = "https://batdongsan.com.vn"
        path = "/ban" if intent.intent == "mua" else "/cho-thue"

        if intent.property_type == "chung cư":
            path += "-can-ho-chung-cu"
        elif intent.property_type == "nhà riêng":
            path += "-nha-rieng"
        else:
            path += "-bat-dong-san"

        path += "-ha-noi"
        search_url = base_url + path

        task = f"""
Tìm kiếm bất động sản trên Batdongsan.com.vn:
1. Truy cập: {search_url}
2. Thu thập 5 listing đầu tiên
3. Cho mỗi listing: tiêu đề, giá, diện tích, địa chỉ, URL

Trả về JSON array:
[{{"title": "...", "price_text": "...", "area_text": "...", "location": "...", "url": "..."}}]
"""

        try:
            agent = Agent(
                task=task,
                llm=self.llm,
                use_vision=settings.browser_use_vision,
                max_actions_per_step=3,
            )

            result = await agent.run(max_steps=5)
            return self._parse_agent_result(result)

        except Exception as e:
            logger.error(f"Batdongsan search error: {e}")
            return []

    def _parse_agent_result(self, result: Any) -> List[Dict]:
        """Parse agent result into list of dicts."""
        try:
            # Handle AgentHistoryList
            if hasattr(result, 'final_result'):
                content = result.final_result()
            elif hasattr(result, 'last_result'):
                content = result.last_result()
            else:
                content = str(result)

            # Already a list
            if isinstance(content, list):
                return content

            # Parse string
            if isinstance(content, str):
                parsed = self._safe_parse_json(content)
                if isinstance(parsed, list):
                    return parsed

                # Try to find JSON array
                match = re.search(r'\[.*\]', content, re.DOTALL)
                if match:
                    try:
                        return json.loads(match.group(0))
                    except:
                        pass

            # Dict with results
            if isinstance(content, dict):
                for key in ['results', 'listings', 'data']:
                    if key in content and isinstance(content[key], list):
                        return content[key]

        except Exception as e:
            logger.warning(f"Parse agent result error: {e}")

        return []

    def _deduplicate_listings(self, listings: List[Dict]) -> List[Dict]:
        """Remove duplicate listings based on URL, title, or phone."""
        seen_urls = set()
        seen_titles = set()
        unique = []

        for listing in listings:
            # Get identifiers
            url = listing.get('url') or listing.get('source_url', '')
            title = listing.get('title', '').lower().strip()[:50]  # First 50 chars
            phone = listing.get('contact', '')

            # Create multiple keys for dedup
            url_key = url if url else None
            title_key = title if title else None

            # Check if duplicate
            is_dup = False
            if url_key and url_key in seen_urls:
                is_dup = True
            if title_key and title_key in seen_titles:
                is_dup = True

            if not is_dup:
                if url_key:
                    seen_urls.add(url_key)
                if title_key:
                    seen_titles.add(title_key)
                unique.append(listing)

        logger.info(f"Deduplicated: {len(listings)} -> {len(unique)} listings")
        return unique

    async def health_check(self) -> Dict:
        """Check LLM health and connection."""
        try:
            start = time.time()

            # Different message format for different LLMs
            if "Gemini" in type(self.llm).__name__ or "Google" in type(self.llm).__name__:
                # Langchain format for Gemini
                from langchain_core.messages import HumanMessage
                response = await self.llm.ainvoke([HumanMessage(content="ping")])
                content = response.content if hasattr(response, 'content') else str(response)
            else:
                # browser-use format for Groq/Ollama
                from browser_use.llm import UserMessage
                response = await self.llm.ainvoke([UserMessage(content="ping")])
                content = response.completion if hasattr(response, 'completion') else str(response)

            elapsed = int((time.time() - start) * 1000)

            return {
                "status": "healthy",
                "llm_type": self.llm_type,
                "llm_class": type(self.llm).__name__,
                "response_time_ms": elapsed,
                "headless": settings.headless_mode,
                "vision_enabled": settings.browser_use_vision,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "llm_type": self.llm_type,
            }

    def get_stats(self) -> Dict:
        """Get current configuration stats."""
        return {
            "llm_mode": settings.llm_mode,
            "llm_type": self.llm_type,
            "model": settings.groq_model if settings.llm_mode == "groq" else settings.ollama_model,
            "headless": settings.headless_mode,
            "vision_enabled": settings.browser_use_vision,
        }
