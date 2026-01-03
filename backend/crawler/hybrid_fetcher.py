"""
Hybrid fetcher that automatically chooses between HTTP and Playwright
based on site characteristics and content quality
"""
import asyncio
from typing import Dict, Optional
from dataclasses import dataclass
from loguru import logger
from urllib.parse import urlparse

from .http_fetcher import HTTPFetcher, PageData
from .fetcher import PageFetcher


# Sites known to require JavaScript rendering
JS_HEAVY_SITES = {
    # News & Media
    'medium.com',
    'substack.com',
    'buzzfeed.com',
    'vox.com',
    
    # Health & Wellness
    'healthline.com',
    'webmd.com',
    'mayoclinic.org',
    
    # E-commerce & Platforms
    'amazon.com',
    'etsy.com',
    'shopify.com',
    
    # Social & Content Platforms
    'blogger.com',
    'wordpress.com',
    'wix.com',
    'squarespace.com',
    'notion.so',
    
    # Modern Web Apps
    'vercel.app',
    'netlify.app',
    'github.io',
    
    # Add more as needed
}

# Patterns that suggest a site might need JavaScript
JS_INDICATORS = [
    'react',
    'vue',
    'angular',
    'next.js',
    'gatsby',
    '__NEXT_DATA__',
    '__nuxt',
    'data-reactroot',
    'ng-version',
]


class HybridFetcher:
    """
    Smart fetcher that tries HTTP first, then Playwright if needed
    
    Strategy:
    1. Check if domain is known JS-heavy → use Playwright
    2. Try HTTP first (fast)
    3. Check if content quality is poor → retry with Playwright
    4. Return best result
    """
    
    def __init__(self):
        self.http_fetcher = HTTPFetcher()
        self.playwright_fetcher = None  # Lazy load
        self.force_playwright = False
        
    async def fetch(self, url: str, take_screenshot: bool = False) -> PageData:
        """
        Fetch page using optimal strategy
        
        Args:
            url: URL to fetch
            take_screenshot: Whether to capture screenshot (Playwright only)
            
        Returns:
            PageData with best available content
        """
        domain = self._get_domain(url)
        
        # Strategy 1: Known JS-heavy site → use Playwright directly
        if self._requires_javascript(domain):
            logger.info(f"Known JS-heavy site: {domain}, using Playwright")
            return await self._fetch_with_playwright(url, take_screenshot)
        
        # Strategy 2: Try HTTP first (fast path)
        logger.info(f"Trying HTTP fetch for: {url}")
        http_result = await self.http_fetcher.fetch(url)
        
        # Check if HTTP result is acceptable
        if http_result.error:
            logger.warning(f"HTTP fetch failed: {http_result.error}, retrying with Playwright")
            return await self._fetch_with_playwright(url, take_screenshot)
        
        # Check content quality
        quality = self._assess_content_quality(http_result)
        
        if quality['score'] < 30:  # Poor quality threshold
            logger.info(
                f"HTTP content quality low ({quality['score']}/100), "
                f"reasons: {quality['reasons']}, retrying with Playwright"
            )
            playwright_result = await self._fetch_with_playwright(url, take_screenshot)
            
            # Compare results and return better one
            pw_quality = self._assess_content_quality(playwright_result)
            if pw_quality['score'] > quality['score']:
                logger.success(
                    f"Playwright improved quality: {quality['score']} → {pw_quality['score']}"
                )
                return playwright_result
            else:
                logger.info("HTTP quality was acceptable after all")
                return http_result
        
        logger.success(f"HTTP fetch successful, quality: {quality['score']}/100")
        return http_result
    
    async def _fetch_with_playwright(self, url: str, take_screenshot: bool) -> PageData:
        """Fetch using Playwright (lazy load)"""
        if self.playwright_fetcher is None:
            self.playwright_fetcher = PageFetcher()
        
        return await self.playwright_fetcher.fetch(url, take_screenshot)
    
    def _requires_javascript(self, domain: str) -> bool:
        """Check if domain requires JavaScript rendering"""
        # Remove www. prefix
        domain = domain.replace('www.', '')
        
        # Check exact matches
        if domain in JS_HEAVY_SITES:
            return True
        
        # Check parent domains (e.g., blog.medium.com → medium.com)
        parts = domain.split('.')
        if len(parts) >= 2:
            parent = '.'.join(parts[-2:])
            if parent in JS_HEAVY_SITES:
                return True
        
        return False
    
    def _assess_content_quality(self, page_data: PageData) -> Dict:
        """
        Assess if fetched content is usable
        
        Returns quality score (0-100) and reasons
        """
        score = 100
        reasons = []
        
        if page_data.error:
            return {'score': 0, 'reasons': ['fetch_error']}
        
        html = page_data.html
        html_lower = html.lower()
        
        # Check 1: Minimum content length
        if len(html) < 1000:
            score -= 30
            reasons.append('too_short')
        
        # Check 2: Looks like JavaScript placeholder
        js_indicators = [
            'noscript',
            'javascript is required',
            'please enable javascript',
            'this site requires javascript',
            '__next_data__',
            'window.__initial',
        ]
        
        indicator_count = sum(1 for indicator in js_indicators if indicator in html_lower)
        if indicator_count >= 2:
            score -= 40
            reasons.append('js_required')
        
        # Check 3: Missing essential content tags
        essential_tags = ['<p', '<h1', '<h2', '<article', '<main']
        missing_tags = sum(1 for tag in essential_tags if tag not in html_lower)
        
        if missing_tags >= 4:
            score -= 30
            reasons.append('missing_structure')
        
        # Check 4: Suspicious patterns (SPA loading screens)
        spa_patterns = [
            'loading...',
            'please wait',
            'initializing',
            '<div id="root"></div>',
            '<div id="app"></div>',
        ]
        
        spa_matches = sum(1 for pattern in spa_patterns if pattern in html_lower)
        if spa_matches >= 2:
            score -= 20
            reasons.append('spa_loading_screen')
        
        # Check 5: Good signs (comprehensive content)
        if len(html) > 10000:
            score = min(100, score + 10)
        
        if html.count('<p') > 10:
            score = min(100, score + 10)
        
        return {
            'score': max(0, score),
            'reasons': reasons if reasons else ['good_quality']
        }
    
    def _get_domain(self, url: str) -> str:
        """Extract domain from URL"""
        return urlparse(url).netloc


# Convenience function
async def fetch_page(url: str, take_screenshot: bool = False) -> PageData:
    """Fetch a page using hybrid strategy"""
    fetcher = HybridFetcher()
    return await fetcher.fetch(url, take_screenshot)


# Example usage and testing
if __name__ == "__main__":
    async def test_sites():
        fetcher = HybridFetcher()
        
        test_urls = [
            "https://example.com",  # Should use HTTP
            "https://www.healthline.com/nutrition/vitamin-d-foods",  # Should use Playwright
            "https://en.wikipedia.org/wiki/Python_(programming_language)",  # Should use HTTP
            "https://medium.com/@example/test-article",  # Should use Playwright
        ]
        
        for url in test_urls:
            print(f"\n{'='*80}")
            print(f"Testing: {url}")
            print('='*80)
            
            try:
                result = await fetcher.fetch(url)
                quality = fetcher._assess_content_quality(result)
                
                print(f"Status: {result.status_code}")
                print(f"HTML Length: {len(result.html):,} chars")
                print(f"Quality Score: {quality['score']}/100")
                print(f"Quality Reasons: {', '.join(quality['reasons'])}")
                print(f"Error: {result.error or 'None'}")
            except Exception as e:
                print(f"❌ Error: {e}")
    
    asyncio.run(test_sites())

