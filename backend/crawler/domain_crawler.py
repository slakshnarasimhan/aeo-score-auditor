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
    
    def __init__(self, max_pages: int = 10, max_depth: int = 5):
        """
        Initialize domain crawler
        
        Args:
            max_pages: Maximum number of pages to crawl (0 or very large number = unlimited)
            max_depth: Maximum depth from starting URL (increased default for better coverage)
        """
        self.max_pages = max_pages if max_pages > 0 else 999999  # Treat 0 as unlimited
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
            # Limit if max_pages is set (if it's 999999, this effectively returns all)
            limited_urls = sitemap_urls[:self.max_pages]
            logger.info(f"Returning {len(limited_urls)} URLs (max_pages={self.max_pages})")
            return limited_urls
        
        # Strategy 2: Crawl from homepage
        logger.info("No sitemap found, crawling from homepage...")
        crawled_urls = await self._crawl_from_page(domain_url, base_domain)
        
        limited_urls = list(crawled_urls)[:self.max_pages]
        logger.info(f"Returning {len(limited_urls)} URLs from crawling (max_pages={self.max_pages})")
        return limited_urls
    
    async def _discover_from_sitemap(self, base_domain: str) -> List[str]:
        """Try to discover URLs from sitemap.xml (recursively handles sitemap indexes)"""
        sitemap_urls = [
            f"{base_domain}/sitemap.xml",
            f"{base_domain}/sitemap_index.xml",
            f"{base_domain}/sitemap-index.xml",
        ]
        
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            for sitemap_url in sitemap_urls:
                try:
                    response = await client.get(sitemap_url)
                    if response.status_code == 200:
                        urls = await self._parse_sitemap_recursive(response.text, client, base_domain)
                        if urls:
                            logger.info(f"Discovered {len(urls)} URLs from sitemap(s)")
                            return urls
                except Exception as e:
                    logger.debug(f"Could not fetch {sitemap_url}: {e}")
        
        return []
    
    async def _parse_sitemap_recursive(self, xml_content: str, client: httpx.AsyncClient, base_domain: str) -> List[str]:
        """Recursively parse sitemap XML and extract URLs (handles sitemap indexes)"""
        try:
            root = ET.fromstring(xml_content)
            
            # Handle sitemap namespace
            namespaces = {
                'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9',
                'xhtml': 'http://www.w3.org/1999/xhtml'
            }
            
            urls = []
            
            # Check if it's a sitemap index (contains <sitemap> entries)
            child_sitemaps = root.findall('.//sm:sitemap/sm:loc', namespaces)
            if child_sitemaps:
                logger.info(f"Found sitemap index with {len(child_sitemaps)} child sitemaps, fetching recursively...")
                # Fetch child sitemaps in batches to avoid overwhelming server
                import asyncio
                batch_size = 5  # Fetch 5 sitemaps concurrently
                
                for i in range(0, len(child_sitemaps), batch_size):
                    batch = child_sitemaps[i:i + batch_size]
                    tasks = []
                    for sitemap_elem in batch:
                        child_sitemap_url = sitemap_elem.text
                        if child_sitemap_url:
                            tasks.append(self._fetch_and_parse_sitemap(child_sitemap_url, client))
                    
                    # Fetch batch of child sitemaps
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Collect URLs from this batch
                    for result in results:
                        if isinstance(result, list):
                            urls.extend(result)
                        elif isinstance(result, Exception):
                            logger.debug(f"Failed to fetch child sitemap: {result}")
                    
                    logger.info(f"Processed {min(i + batch_size, len(child_sitemaps))}/{len(child_sitemaps)} child sitemaps, found {len(urls)} URLs so far...")
                    
                    # Small delay between batches to be respectful
                    if i + batch_size < len(child_sitemaps):
                        await asyncio.sleep(0.5)
                
                logger.info(f"Extracted {len(urls)} URLs from {len(child_sitemaps)} child sitemaps")
                return urls
            
            # Extract regular URLs from a regular sitemap
            for url_elem in root.findall('.//sm:url/sm:loc', namespaces):
                if url_elem.text:
                    url = url_elem.text.strip()
                    # Filter out non-page URLs
                    if self._is_valid_page_url(url):
                        urls.append(url)
            
            return urls
            
        except Exception as e:
            logger.debug(f"Failed to parse sitemap: {e}")
            return []
    
    async def _fetch_and_parse_sitemap(self, sitemap_url: str, client: httpx.AsyncClient) -> List[str]:
        """Fetch a child sitemap and extract URLs from it"""
        try:
            response = await client.get(sitemap_url, timeout=30.0)
            if response.status_code == 200:
                # Parse this sitemap (which should be a regular sitemap, not an index)
                root = ET.fromstring(response.text)
                namespaces = {
                    'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'
                }
                urls = []
                
                # Extract URLs
                for url_elem in root.findall('.//sm:url/sm:loc', namespaces):
                    if url_elem.text:
                        url = url_elem.text.strip()
                        # Filter out non-page URLs
                        if self._is_valid_page_url(url):
                            urls.append(url)
                
                return urls
            return []
        except Exception as e:
            logger.debug(f"Failed to fetch child sitemap {sitemap_url}: {e}")
            return []
    
    def _is_valid_page_url(self, url: str) -> bool:
        """Check if URL is a valid page URL (not XML, images, etc.)"""
        url_lower = url.lower()
        # Exclude non-page file extensions
        excluded_extensions = [
            '.xml', '.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg',
            '.pdf', '.zip', '.tar', '.gz', '.css', '.js', '.json',
            '.ico', '.woff', '.woff2', '.ttf', '.eot'
        ]
        
        # Exclude sitemap files
        if '/sitemap' in url_lower and url_lower.endswith('.xml'):
            return False
        
        # Check for excluded extensions
        for ext in excluded_extensions:
            if url_lower.endswith(ext):
                return False
        
        return True
    
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
    
    def __init__(self, max_pages: int = 100, max_concurrent: int = 3, job_id: Optional[str] = None):
        """
        Initialize orchestrator
        
        Args:
            max_pages: Maximum pages to audit (default: 100, set to 0 for unlimited)
            max_concurrent: Maximum concurrent audits
            job_id: Job ID for progress tracking
        """
        self.max_pages = max_pages if max_pages > 0 else 9999
        self.max_concurrent = max_concurrent
        self.crawler = DomainCrawler(max_pages=self.max_pages)
        self.job_id = job_id
        self.tracker = None
        
        if job_id:
            from progress_tracker import progress_tracker
            self.tracker = progress_tracker
    
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
        
        # Report progress: discovering
        if self.tracker and self.job_id:
            self.tracker.update(
                self.job_id,
                status="discovering",
                current_step="Discovering URLs from sitemap or crawling...",
                message=f"Analyzing {domain_url}"
            )
        
        # Step 1: Discover URLs
        urls = await self.crawler.discover_urls(domain_url)
        logger.info(f"Discovered {len(urls)} URLs to audit")
        
        if not urls:
            if self.tracker and self.job_id:
                self.tracker.complete_job(self.job_id, success=False, message="No URLs discovered")
            return {
                'domain': domain_url,
                'error': 'No URLs discovered',
                'pages_audited': 0
            }
        
        # Report progress: URLs discovered
        if self.tracker and self.job_id:
            self.tracker.update(
                self.job_id,
                status="auditing",
                current_step=f"Auditing {len(urls)} pages...",
                total_urls=len(urls),
                urls_discovered=len(urls),
                message=f"Found {len(urls)} pages to audit"
            )
        
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
                
                # Report progress after each page
                if self.tracker and self.job_id:
                    self.tracker.update(
                        self.job_id,
                        pages_audited=len(page_results),
                        current_url=url,
                        message=f"Audited {len(page_results)}/{len(urls)} pages"
                    )
            
            logger.info(f"Audited {len(page_results)}/{len(urls)} pages...")
        
        # Step 3: Aggregate results
        aggregated = self._aggregate_results(domain_url, page_results)
        
        # Report completion
        if self.tracker and self.job_id:
            self.tracker.complete_job(
                self.job_id,
                success=True,
                message=f"Completed! Average score: {aggregated['overall_score']}/100"
            )
        
        logger.info(f"Domain audit complete: {aggregated['overall_score']}/100")
        return aggregated
    
    def _aggregate_results(self, domain_url: str, page_results: List[Dict]) -> Dict:
        """Aggregate results from multiple pages with detailed per-page breakdown"""
        
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
        
        # Aggregate breakdown scores with per-page details
        breakdown = {}
        first_result = valid_results[0]
        
        for category, score_data in first_result.get('breakdown', {}).items():
            # Collect all scores and page details for this category
            page_scores = []
            for r in valid_results:
                if category in r.get('breakdown', {}):
                    cat_data = r['breakdown'][category]
                    page_scores.append({
                        'url': r['url'],
                        'score': cat_data['score'],
                        'percentage': cat_data.get('percentage', 0),
                        'sub_scores': cat_data.get('sub_scores', {})
                    })
            
            if page_scores:
                avg_category_score = sum(p['score'] for p in page_scores) / len(page_scores)
                breakdown[category] = {
                    'score': round(avg_category_score, 1),
                    'max': score_data['max'],
                    'percentage': round((avg_category_score / score_data['max']) * 100, 1),
                    'page_scores': page_scores,  # Per-page scores for this category
                    'best_page': max(page_scores, key=lambda x: x['score']),
                    'worst_page': min(page_scores, key=lambda x: x['score'])
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

