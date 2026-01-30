"""
Base Crawler wrapper cho Crawl4AI
Cung cấp common functionality cho tất cả crawlers
"""

import asyncio
import sys
from typing import List, Dict, Optional, Any
from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai.extraction_strategy import LLMExtractionStrategy, JsonCssExtractionStrategy
from langchain_groq import ChatGroq
import os
from config import settings

# Fix for Python 3.13 on Windows - Playwright compatibility
if sys.platform == 'win32' and sys.version_info >= (3, 13):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class BaseCrawler:
    """Base crawler với Crawl4AI"""

    def __init__(self):
        self.llm = self._init_llm()

    def _init_llm(self):
        """Initialize Groq LLM"""
        return ChatGroq(
            model=settings.groq_model,
            api_key=settings.groq_api_key,
            temperature=0.1
        )

    async def crawl_url(
        self,
        url: str,
        css_selector: Optional[str] = None,
        extraction_strategy: Optional[Any] = None,
        wait_for: Optional[str] = None
    ) -> Dict:
        """
        Crawl single URL với Crawl4AI

        Args:
            url: URL to crawl
            css_selector: CSS selector để filter content
            extraction_strategy: Custom extraction strategy
            wait_for: CSS selector to wait for before extraction

        Returns:
            Dict with: html, markdown, extracted_content, links, metadata
        """

        try:
            async with AsyncWebCrawler(verbose=False) as crawler:
                result = await crawler.arun(
                    url=url,
                    cache_mode=CacheMode.ENABLED,
                    css_selector=css_selector,
                    extraction_strategy=extraction_strategy,
                    word_count_threshold=10,
                    verbose=False
                )

                if not result.success:
                    print(f"❌ Crawl failed: {url}")
                    return None

                return {
                    'url': url,
                    'html': result.html,
                    'markdown': result.markdown,
                    'extracted_content': result.extracted_content,
                    'links': result.links.get('internal', []) if result.links else [],
                    'metadata': result.metadata,
                    'success': True
                }

        except Exception as e:
            print(f"❌ Crawl error for {url}: {e}")
            return None

    async def crawl_multiple(
        self,
        urls: List[str],
        max_concurrent: int = 5,
        **kwargs
    ) -> List[Dict]:
        """
        Crawl multiple URLs in parallel

        Args:
            urls: List of URLs
            max_concurrent: Max parallel requests
            **kwargs: Additional args for crawl_url()

        Returns:
            List of crawl results
        """

        print(f"🚀 Crawling {len(urls)} URLs (max {max_concurrent} concurrent)...")

        # Create semaphore for rate limiting
        semaphore = asyncio.Semaphore(max_concurrent)

        async def crawl_with_semaphore(url):
            async with semaphore:
                result = await self.crawl_url(url, **kwargs)
                await asyncio.sleep(0.5)  # Small delay
                return result

        tasks = [crawl_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter successful results
        successful = [r for r in results if r and isinstance(r, dict) and r.get('success')]

        print(f"✅ Successfully crawled {len(successful)}/{len(urls)} URLs")

        return successful

    def create_css_extraction(self, schema: Dict) -> JsonCssExtractionStrategy:
        """
        Create CSS-based extraction strategy

        Args:
            schema: Dict mapping field names to CSS selectors
            Example:
            {
                "title": "h1.title",
                "price": ".price-tag",
                "location": ".address"
            }
        """
        return JsonCssExtractionStrategy(schema)

    def create_llm_extraction(self, instruction: str, schema: Optional[Dict] = None) -> LLMExtractionStrategy:
        """
        Create LLM-based extraction strategy

        Args:
            instruction: Natural language instruction for LLM
            schema: Optional Pydantic schema for structured output
        """
        return LLMExtractionStrategy(
            provider=self.llm,
            instruction=instruction,
            schema=schema
        )
