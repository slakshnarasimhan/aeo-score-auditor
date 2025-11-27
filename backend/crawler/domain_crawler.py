"""
Domain-wide crawler for discovering and auditing multiple pages
"""
import asyncio
from typing import List, Set, Dict, Optional
from urllib.parse import urljoin, urlparse, urlunparse
from loguru import logger
import xml.etree.ElementTree as ET
import httpx
from bs4 import BeautifulSoup


class DomainCrawler:
    """Discovers URLs across a domain"""
    
    def __init__(self, max_pages: int = 10, max_depth: int = 2):
        """
        Initialize domain crawler
        
        Args:
            max_pages: Maximum number of pages to crawl
            max_depth: Maximum depth from starting URL
        """
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.visited: Set[str] = set()
        self.discovered: Set[str] = set()
    
    async def discover_urls(self, domain_url: str) -> List[str]:
        """
        Discover URLs from a domain
        
        Args:
            domain_url: Starting domain URL (e.g., https://example.com)
            
        Returns:
            List of discovered URLs
        """
        logger.info(f"Starting URL discovery for domain: {domain_url}")
        
        # Parse domain
        parsed = urlparse(domain_url)
        base_domain = f"{parsed.scheme}://{parsed.netloc}"
        
        # Strategy 1: Try sitemap first (fastest)
        sitemap_urls = await self._discover_from_sitemap(base_domain)
        if sitemap_urls:
            logger.info(f"Discovered {len(sitemap_urls)} URLs from sitemap")
            return sitemap_urls[:self.max_pages]
        
        # Strategy 2: Crawl from homepage
        logger.info("No sitemap found, crawling from homepage...")
        crawled_urls = await self._crawl_from_page(domain_url, base_domain)
        
        return list(crawled_urls)[:self.max_pages]
    
    async def _discover_from_sitemap(self, base_domain: str) -> List[str]:
        """Try to discover URLs from sitemap.xml"""
        sitemap_urls = [
            f"{base_domain}/sitemap.xml",
            f"{base_domain}/sitemap_index.xml",
            f"{base_domain}/sitemap-index.xml",
        ]
        
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            for sitemap_url in sitemap_urls:
                try:
                    response = await client.get(sitemap_url)
                    if response.status_code == 200:
                        urls = self._parse_sitemap(response.text)
                        if urls:
                            return urls
                except Exception as e:
                    logger.debug(f"Could not fetch {sitemap_url}: {e}")
        
        return []
    
    def _parse_sitemap(self, xml_content: str) -> List[str]:
        """Parse sitemap XML and extract URLs"""
        try:
            root = ET.fromstring(xml_content)
            
            # Handle sitemap namespace
            namespaces = {
                'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9',
                'xhtml': 'http://www.w3.org/1999/xhtml'
            }
            
            urls = []
            
            # Check if it's a sitemap index
            for sitemap in root.findall('.//sm:sitemap/sm:loc', namespaces):
                urls.append(sitemap.text)
            
            # Extract regular URLs
            for url in root.findall('.//sm:url/sm:loc', namespaces):
                if url.text:
                    urls.append(url.text)
            
            return urls
            
        except Exception as e:
            logger.debug(f"Failed to parse sitemap: {e}")
            return []
    
    async def _crawl_from_page(self, start_url: str, base_domain: str) -> Set[str]:
        """Crawl URLs from a starting page"""
        to_visit = [(start_url, 0)]  # (url, depth)
        discovered = set()
        
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            while to_visit and len(discovered) < self.max_pages:
                url, depth = to_visit.pop(0)
                
                if url in self.visited or depth > self.max_depth:
                    continue
                
                self.visited.add(url)
                
                try:
                    # Fetch page
                    response = await client.get(url, headers={
                        'User-Agent': 'Mozilla/5.0 (compatible; AEOScoreBot/1.0)'
                    })
                    
                    if response.status_code != 200:
                        continue
                    
                    discovered.add(url)
                    
                    # Parse and find more links
                    if depth < self.max_depth:
                        soup = BeautifulSoup(response.text, 'lxml')
                        links = self._extract_links(soup, url, base_domain)
                        
                        for link in links:
                            if link not in self.visited and link not in [u for u, d in to_visit]:
                                to_visit.append((link, depth + 1))
                    
                    logger.debug(f"Discovered {len(discovered)} URLs so far...")
                    
                except Exception as e:
                    logger.debug(f"Failed to crawl {url}: {e}")
        
        return discovered
    
    def _extract_links(self, soup: BeautifulSoup, current_url: str, base_domain: str) -> List[str]:
        """Extract valid links from a page"""
        links = []
        parsed_base = urlparse(base_domain)
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            
            # Convert to absolute URL
            absolute_url = urljoin(current_url, href)
            parsed = urlparse(absolute_url)
            
            # Only include same-domain links
            if parsed.netloc == parsed_base.netloc:
                # Remove fragments
                clean_url = urlunparse((
                    parsed.scheme,
                    parsed.netloc,
                    parsed.path,
                    parsed.params,
                    parsed.query,
                    ''  # Remove fragment
                ))
                
                # Skip common non-content URLs
                skip_patterns = [
                    '/login', '/logout', '/signin', '/signup',
                    '/cart', '/checkout', '/account',
                    '.pdf', '.jpg', '.png', '.gif', '.zip'
                ]
                
                if not any(pattern in clean_url.lower() for pattern in skip_patterns):
                    links.append(clean_url)
        
        return list(set(links))  # Remove duplicates


class DomainAuditOrchestrator:
    """Orchestrates auditing multiple pages across a domain"""
    
    def __init__(self, max_pages: int = 10, max_concurrent: int = 3):
        """
        Initialize orchestrator
        
        Args:
            max_pages: Maximum pages to audit
            max_concurrent: Maximum concurrent audits
        """
        self.max_pages = max_pages
        self.max_concurrent = max_concurrent
        self.crawler = DomainCrawler(max_pages=max_pages)
    
    async def audit_domain(self, domain_url: str) -> Dict:
        """
        Audit entire domain
        
        Args:
            domain_url: Domain to audit
            
        Returns:
            Aggregated audit results
        """
        from audit_pipeline import AuditPipeline
        
        logger.info(f"Starting domain audit for: {domain_url}")
        
        # Step 1: Discover URLs
        urls = await self.crawler.discover_urls(domain_url)
        logger.info(f"Discovered {len(urls)} URLs to audit")
        
        if not urls:
            return {
                'domain': domain_url,
                'error': 'No URLs discovered',
                'pages_audited': 0
            }
        
        # Step 2: Audit each page (with concurrency limit)
        pipeline = AuditPipeline()
        page_results = []
        
        # Process in batches
        for i in range(0, len(urls), self.max_concurrent):
            batch = urls[i:i + self.max_concurrent]
            batch_tasks = [pipeline.audit_page(url) for url in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            for url, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Failed to audit {url}: {result}")
                    page_results.append({
                        'url': url,
                        'error': str(result),
                        'overall_score': 0
                    })
                else:
                    page_results.append(result)
            
            logger.info(f"Audited {len(page_results)}/{len(urls)} pages...")
        
        # Step 3: Aggregate results
        aggregated = self._aggregate_results(domain_url, page_results)
        
        logger.info(f"Domain audit complete: {aggregated['overall_score']}/100")
        return aggregated
    
    def _aggregate_results(self, domain_url: str, page_results: List[Dict]) -> Dict:
        """Aggregate results from multiple pages"""
        
        # Filter out errors
        valid_results = [r for r in page_results if 'overall_score' in r and r['overall_score'] > 0]
        
        if not valid_results:
            return {
                'domain': domain_url,
                'overall_score': 0,
                'grade': 'F',
                'pages_audited': len(page_results),
                'pages_successful': 0,
                'error': 'No pages could be audited successfully'
            }
        
        # Calculate averages
        avg_score = sum(r['overall_score'] for r in valid_results) / len(valid_results)
        
        # Aggregate breakdown scores
        breakdown = {}
        first_result = valid_results[0]
        
        for category, score_data in first_result.get('breakdown', {}).items():
            category_scores = [r['breakdown'][category]['score'] 
                             for r in valid_results 
                             if category in r.get('breakdown', {})]
            
            if category_scores:
                breakdown[category] = {
                    'score': round(sum(category_scores) / len(category_scores), 1),
                    'max': score_data['max'],
                    'percentage': round((sum(category_scores) / len(category_scores) / score_data['max']) * 100, 1)
                }
        
        # Determine grade
        if avg_score >= 90:
            grade = 'A+'
        elif avg_score >= 80:
            grade = 'A'
        elif avg_score >= 70:
            grade = 'B+'
        elif avg_score >= 60:
            grade = 'B'
        elif avg_score >= 50:
            grade = 'C'
        else:
            grade = 'F'
        
        return {
            'domain': domain_url,
            'overall_score': round(avg_score, 1),
            'grade': grade,
            'pages_audited': len(page_results),
            'pages_successful': len(valid_results),
            'breakdown': breakdown,
            'page_results': valid_results,  # Include individual page results
            'best_page': max(valid_results, key=lambda x: x['overall_score']),
            'worst_page': min(valid_results, key=lambda x: x['overall_score'])
        }

