"""
HTTP-based page fetcher (alternative to Playwright)
Works for static pages and basic content extraction
"""
import httpx
from typing import Dict, Optional
from dataclasses import dataclass
from loguru import logger
import time


@dataclass
class PageData:
    """Fetched page data"""
    url: str
    final_url: str
    html: str
    status_code: int
    performance: Dict
    screenshot: Optional[bytes] = None
    error: Optional[str] = None


class HTTPFetcher:
    """Fetches web pages using HTTP requests"""
    
    def __init__(self):
        self.user_agent = "Mozilla/5.0 (compatible; AEOScoreBot/1.0; +https://aeoscore.com)"
        self.timeout = 30.0
        self.max_retries = 3
    
    async def fetch(self, url: str, take_screenshot: bool = False) -> PageData:
        """
        Fetch a page using HTTP
        
        Args:
            url: URL to fetch
            take_screenshot: Ignored for HTTP fetcher
            
        Returns:
            PageData object with fetched content
        """
        for attempt in range(self.max_retries):
            try:
                return await self._fetch_with_httpx(url)
            except Exception as e:
                logger.warning(f"Fetch attempt {attempt + 1} failed for {url}: {e}")
                if attempt == self.max_retries - 1:
                    return PageData(
                        url=url,
                        final_url=url,
                        html="",
                        status_code=0,
                        performance={},
                        error=str(e)
                    )
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    async def _fetch_with_httpx(self, url: str) -> PageData:
        """Internal fetch implementation"""
        start_time = time.time()
        
        async with httpx.AsyncClient(follow_redirects=True, timeout=self.timeout) as client:
            headers = {
                'User-Agent': self.user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }
            
            response = await client.get(url, headers=headers)
            
            end_time = time.time()
            
            # Basic performance metrics
            performance = {
                'ttfb': (end_time - start_time) * 1000,  # Time to first byte in ms
                'page_load': (end_time - start_time) * 1000,
                'dom_load': (end_time - start_time) * 1000,
                'fcp': None,  # Not available without browser
            }
            
            logger.info(f"Successfully fetched {url} (status: {response.status_code})")
            
            return PageData(
                url=url,
                final_url=str(response.url),
                html=response.text,
                status_code=response.status_code,
                performance=performance,
                screenshot=None
            )


# For async usage
import asyncio


async def fetch_page(url: str) -> PageData:
    """Convenience function to fetch a page"""
    fetcher = HTTPFetcher()
    return await fetcher.fetch(url)


# Example usage
if __name__ == "__main__":
    async def main():
        result = await fetch_page("https://example.com")
        print(f"Fetched: {result.url}")
        print(f"Status: {result.status_code}")
        print(f"HTML length: {len(result.html)}")
        print(f"Performance: {result.performance}")
    
    asyncio.run(main())

