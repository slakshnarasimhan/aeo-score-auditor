"""
Page fetcher using Playwright
"""
from typing import Dict, Optional
from dataclasses import dataclass
from playwright.async_api import async_playwright, Page, Browser
from loguru import logger
import asyncio

from config import settings


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


class PageFetcher:
    """Fetches and renders web pages"""
    
    def __init__(self):
        self.user_agent = settings.CRAWLER_USER_AGENT
        self.timeout = settings.CRAWLER_TIMEOUT
        self.max_retries = settings.CRAWLER_MAX_RETRIES
    
    async def fetch(self, url: str, take_screenshot: bool = False) -> PageData:
        """
        Fetch and render a page
        
        Args:
            url: URL to fetch
            take_screenshot: Whether to capture screenshot
            
        Returns:
            PageData object with fetched content
        """
        for attempt in range(self.max_retries):
            try:
                return await self._fetch_with_playwright(url, take_screenshot)
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
    
    async def _fetch_with_playwright(self, url: str, take_screenshot: bool) -> PageData:
        """Internal fetch implementation"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Set user agent
            await page.set_extra_http_headers({
                'User-Agent': self.user_agent
            })
            
            # Navigate to page
            response = await page.goto(
                url,
                wait_until='networkidle',
                timeout=self.timeout
            )
            
            # Wait for dynamic content
            await page.wait_for_timeout(2000)
            
            # Get HTML content
            html_content = await page.content()
            
            # Get final URL (after redirects)
            final_url = page.url
            
            # Get performance metrics
            performance = await self._get_performance_metrics(page)
            
            # Get status code
            status_code = response.status if response else 0
            
            # Take screenshot if requested
            screenshot = None
            if take_screenshot:
                screenshot = await page.screenshot(type='png', full_page=False)
            
            await browser.close()
            
            logger.info(f"Successfully fetched {url} (status: {status_code})")
            
            return PageData(
                url=url,
                final_url=final_url,
                html=html_content,
                status_code=status_code,
                performance=performance,
                screenshot=screenshot
            )
    
    async def _get_performance_metrics(self, page: Page) -> Dict:
        """Extract performance metrics from page"""
        try:
            metrics = await page.evaluate('''() => {
                const perf = performance.timing;
                const paint = performance.getEntriesByType('paint');
                return {
                    ttfb: perf.responseStart - perf.requestStart,
                    dom_load: perf.domContentLoadedEventEnd - perf.navigationStart,
                    page_load: perf.loadEventEnd - perf.navigationStart,
                    fcp: paint.find(p => p.name === 'first-contentful-paint')?.startTime || null,
                }
            }''')
            return metrics
        except Exception as e:
            logger.warning(f"Could not get performance metrics: {e}")
            return {}


# Example usage
async def main():
    fetcher = PageFetcher()
    result = await fetcher.fetch("https://example.com")
    print(f"Fetched: {result.url}")
    print(f"Status: {result.status_code}")
    print(f"HTML length: {len(result.html)}")
    print(f"Performance: {result.performance}")


if __name__ == "__main__":
    asyncio.run(main())

