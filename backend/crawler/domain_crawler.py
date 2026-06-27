"""
Domain-wide crawler for discovering and auditing multiple pages
"""
import asyncio
from typing import Callable, List, Set, Dict, Optional
from urllib.parse import urljoin, urlparse, urlunparse
from loguru import logger
import xml.etree.ElementTree as ET
import httpx
from bs4 import BeautifulSoup


class DomainCrawler:
    """Discovers URLs across a domain"""
    
    def __init__(
        self,
        max_pages: int = 10,
        max_depth: int = 5,
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ):
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
        self.progress_callback = progress_callback
        self.last_discovery_error = ""

    def _report_discovery_progress(self, count: int, message: str):
        if self.progress_callback:
            self.progress_callback(min(count, self.max_pages), message)
    
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
        
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, verify=False) as client:
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
                    self._report_discovery_progress(
                        len(urls),
                        f"Processed {min(i + batch_size, len(child_sitemaps))}/{len(child_sitemaps)} sitemaps"
                    )
                    
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
                        if len(urls) % 10 == 0:
                            self._report_discovery_progress(len(urls), f"Found {len(urls)} URLs in sitemap")
            
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
        
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, verify=False) as client:
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
                        if url == start_url and response.status_code in {401, 403, 429}:
                            self.last_discovery_error = self._blocked_message(
                                response.status_code,
                                response.text,
                            )
                        continue
                    
                    discovered.add(url)
                    self._report_discovery_progress(len(discovered), f"Found {len(discovered)} URLs while crawling")
                    
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

    def _blocked_message(self, status_code: int, html: str) -> str:
        html_l = (html or "").lower()
        provider = ""
        if "akamai" in html_l or "edgesuite" in html_l:
            provider = " by Akamai"
        elif "cloudflare" in html_l:
            provider = " by Cloudflare"
        return (
            f"Automated access was blocked{provider} (HTTP {status_code}). "
            "The crawler could not read the homepage or discover links. "
            "Use a previously saved local crawl, or audit an exported HTML copy."
        )
    
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
    
    def __init__(
        self,
        max_pages: int = 100,
        max_concurrent: int = 3,
        job_id: Optional[str] = None,
        options: Optional[Dict] = None,
    ):
        """
        Initialize orchestrator
        
        Args:
            max_pages: Maximum pages to audit (default: 100, set to 0 for unlimited)
            max_concurrent: Maximum concurrent audits
            job_id: Job ID for progress tracking
        """
        self.max_pages = max_pages if max_pages > 0 else 9999
        self.max_concurrent = max_concurrent
        self.job_id = job_id
        self.options = options or {}
        self.tracker = None
        
        if job_id:
            from progress_tracker import progress_tracker
            self.tracker = progress_tracker
        self.crawler = DomainCrawler(
            max_pages=self.max_pages,
            progress_callback=self._update_discovery_progress,
        )

    def _update_discovery_progress(self, urls_discovered: int, message: str):
        if self.tracker and self.job_id:
            self.tracker.update(
                self.job_id,
                status="discovering",
                current_step=message,
                urls_discovered=urls_discovered,
                message=message,
            )
    
    async def audit_domain(self, domain_url: str) -> Dict:
        """
        Audit entire domain
        
        Args:
            domain_url: Domain to audit
            
        Returns:
            Aggregated audit results
        """
        from audit_pipeline import AuditPipeline
        from reporting.domain_intelligence import (
            DomainIntelligencePreflight,
            DomainStrategySynthesizer,
            prioritize_urls_with_intelligence,
        )
        
        logger.info(f"Starting domain audit for: {domain_url}")
        domain_intelligence = {}
        use_local_crawl = bool(
            self.options.get('use_local_crawl') or self.options.get('local_crawl_only')
        )
        run_preflight = not (
            use_local_crawl
            and not self.options.get("run_domain_intelligence_for_local_crawl")
        )
        
        # Report progress: intelligence preflight
        if run_preflight and self.tracker and self.job_id:
            self.tracker.update(
                self.job_id,
                status="intelligence",
                current_step="Building domain intelligence preflight...",
                message=f"Understanding {domain_url} before crawling"
            )
        if run_preflight:
            try:
                intelligence_options = dict(self.options)
                if use_local_crawl:
                    from crawler.crawl_store import build_cached_domain_evidence

                    intelligence_options["domain_evidence"] = build_cached_domain_evidence(
                        domain_url
                    )
                preflight = DomainIntelligencePreflight(
                    model=(
                        self.options.get("domain_intelligence_model")
                        or self.options.get("analysis_model")
                    )
                )
                domain_intelligence = await asyncio.to_thread(
                    preflight.analyze,
                    domain_url,
                    intelligence_options,
                )
            except Exception as e:
                logger.warning(f"Domain intelligence preflight failed: {e}")
        elif self.tracker and self.job_id:
            self.tracker.update(
                self.job_id,
                status="discovering",
                current_step="Loading URLs from local crawl cache...",
                message="Skipping domain intelligence preflight for local crawl"
            )

        # Report progress: discovering
        if self.tracker and self.job_id:
            self.tracker.update(
                self.job_id,
                status="discovering",
                current_step="Discovering URLs from sitemap or crawling...",
                message=f"Analyzing {domain_url}"
            )
        
        # Step 1: Discover URLs or reuse local cache
        if use_local_crawl:
            from crawler.crawl_store import list_cached_urls

            urls = list_cached_urls(domain_url)[:self.max_pages]
            logger.info(f"Loaded {len(urls)} cached URLs for {domain_url}")
        else:
            original_crawler_limit = self.crawler.max_pages
            if self.max_pages > 0 and self.max_pages < 9999 and domain_intelligence:
                self.crawler.max_pages = min(max(self.max_pages * 5, self.max_pages), 1000)
            urls = await self.crawler.discover_urls(domain_url)
            self.crawler.max_pages = original_crawler_limit
            if domain_intelligence:
                urls = prioritize_urls_with_intelligence(
                    urls,
                    domain_intelligence,
                    self.max_pages,
                )
        logger.info(f"Discovered {len(urls)} URLs to audit")
        
        if not urls:
            discovery_error = self.crawler.last_discovery_error
            if self.tracker and self.job_id:
                self.tracker.complete_job(
                    self.job_id,
                    success=False,
                    message=discovery_error or "No URLs discovered",
                )
            return {
                'domain': domain_url,
                'error': (
                    'No local crawl cache found. Run a normal crawl first.'
                    if use_local_crawl
                    else discovery_error or 'No URLs discovered'
                ),
                'discovery_blocked': bool(discovery_error),
                'pages_audited': 0
            }
        
        # Report progress: URLs discovered
        if self.tracker and self.job_id:
            logger.info(f"Updating progress: discovered {len(urls)} URLs, switching to auditing phase")
            self.tracker.update(
                self.job_id,
                status="auditing",
                current_step=f"Auditing {len(urls)} pages...",
                total_urls=len(urls),
                urls_discovered=len(urls),
                message=f"Found {len(urls)} pages to audit"
            )
        else:
            logger.warning(f"Cannot update progress: tracker={self.tracker}, job_id={self.job_id}")
        
        # Step 2: Audit each page (with concurrency limit)
        pipeline = AuditPipeline()
        page_results = []
        page_options = dict(self.options)
        page_options["llm_prompt_eval"] = False
        page_options["external_aeo_validation"] = False
        
        # Process in batches
        for i in range(0, len(urls), self.max_concurrent):
            batch = urls[i:i + self.max_concurrent]
            batch_tasks = [pipeline.audit_page(url, page_options) for url in batch]
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
                    logger.debug(f"Updating progress: {len(page_results)}/{len(urls)} pages audited")
                    self.tracker.update(
                        self.job_id,
                        pages_audited=len(page_results),
                        current_url=url,
                        message=f"Audited {len(page_results)}/{len(urls)} pages"
                    )
                else:
                    logger.warning(f"Tracker not available: tracker={self.tracker}, job_id={self.job_id}")
            
            logger.info(f"Audited {len(page_results)}/{len(urls)} pages...")
        
        valid_results = [
            result for result in page_results
            if result.get("overall_score", 0) > 0
        ]
        final_strategy = domain_intelligence
        run_final_strategy = not (
            use_local_crawl
            and not self.options.get("run_strategy_for_local_crawl")
        )
        if valid_results and run_final_strategy:
            if self.tracker and self.job_id:
                self.tracker.update(
                    self.job_id,
                    status="strategy",
                    current_step="Building final question strategy...",
                    pages_audited=len(page_results),
                    total_urls=len(urls),
                    message="Synthesizing crawled evidence into buyer questions",
                )
            try:
                from crawler.crawl_store import build_page_results_evidence

                synthesizer = DomainStrategySynthesizer(
                    model=self.options.get("strategy_model") or "auto"
                )
                final_strategy = await asyncio.to_thread(
                    synthesizer.analyze,
                    domain_url,
                    build_page_results_evidence(valid_results),
                    domain_intelligence,
                )
            except Exception as e:
                logger.warning(f"Final domain strategy failed: {e}")
        elif valid_results and self.tracker and self.job_id:
            self.tracker.update(
                self.job_id,
                status="finalizing",
                current_step="Finalizing report...",
                pages_audited=len(page_results),
                total_urls=len(urls),
                message="Skipping final strategy synthesis for local crawl",
            )

        # Step 3: Aggregate results
        aggregated = await asyncio.to_thread(
            self._aggregate_results,
            domain_url,
            page_results,
            domain_intelligence,
            final_strategy,
        )
        try:
            from crawler.crawl_store import persist_domain_audit

            aggregated['crawl_artifact_path'] = persist_domain_audit(
                domain_url,
                self.job_id,
                urls,
                page_results,
                aggregated,
            )
        except Exception as e:
            logger.warning(f"Failed to persist domain crawl data: {e}")
        
        # Report aggregation. The route stores the result before marking the
        # job complete so SSE listeners can reliably fetch the final payload.
        if self.tracker and self.job_id:
            self.tracker.update(
                self.job_id,
                status="finalizing",
                current_step="Finalizing report...",
                pages_audited=len(page_results),
                total_urls=len(urls),
                message=f"Calculated average score: {aggregated['overall_score']}/100"
            )
        
        logger.info(f"Domain audit complete: {aggregated['overall_score']}/100")
        return aggregated
    
    def _aggregate_results(
        self,
        domain_url: str,
        page_results: List[Dict],
        domain_intelligence: Dict | None = None,
        domain_strategy: Dict | None = None,
    ) -> Dict:
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
                    'applicability': score_data.get('applicability', 'medium'),
                    'applicability_reason': score_data.get('applicability_reason', ''),
                    'page_scores': page_scores,  # Per-page scores for this category
                    'best_page': max(page_scores, key=lambda x: x['score']),
                    'worst_page': min(page_scores, key=lambda x: x['score'])
                }

        audit_profiles = {}
        for result in valid_results:
            profile_type = (result.get('audit_profile') or {}).get('type', 'general')
            audit_profiles[profile_type] = audit_profiles.get(profile_type, 0) + 1

        content_types = {}
        for result in valid_results:
            content_type = (result.get('content_classification') or {}).get('type', 'unknown')
            content_types[content_type] = content_types.get(content_type, 0) + 1

        primary_profile = first_result.get('audit_profile')
        extraction_goals = first_result.get('extraction_goals', [])
        not_applicable = first_result.get('not_applicable', [])
        
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
        
        aggregated = {
            'domain': domain_url,
            'domain_intelligence': domain_intelligence or {},
            'domain_strategy': domain_strategy or domain_intelligence or {},
            'overall_score': round(avg_score, 1),
            'grade': grade,
            'pages_audited': len(page_results),
            'pages_successful': len(valid_results),
            'breakdown': breakdown,
            'page_results': valid_results,  # Include individual page results
            'best_page': max(valid_results, key=lambda x: x['overall_score']),
            'worst_page': min(valid_results, key=lambda x: x['overall_score']),
            'audit_profile': primary_profile,
            'audit_profile_distribution': audit_profiles,
            'content_type_distribution': content_types,
            'extraction_goals': extraction_goals,
            'not_applicable': not_applicable,
        }

        try:
            from reporting.recommendation_generator import RecommendationGenerator
            aggregated['recommendations'] = RecommendationGenerator().generate_extraction_recommendations(aggregated)
        except Exception as e:
            logger.warning(f"Failed to generate domain recommendations: {e}")
            aggregated['recommendations'] = []

        try:
            from reporting.prompt_gap_analyzer import PromptGapAnalyzer
            from reporting.positioning_analyzer import PositioningAnalyzer
            from reporting.domain_intelligence import merge_intelligence_into_site_context
            from reporting.site_context import load_site_context

            site_context = load_site_context(
                domain_url,
                self.options.get('site_context')
                or self.options.get('supplemental_context')
                or self.options.get('site_context_path')
                or self.options.get('supplemental_context_path'),
            )
            site_context = merge_intelligence_into_site_context(
                site_context,
                domain_strategy or domain_intelligence or {},
            )
            site_context["_answerability_model"] = (
                self.options.get("domain_intelligence_model")
                or self.options.get("analysis_model")
                or "auto"
            )
            aggregated['positioning_analysis'] = PositioningAnalyzer().analyze(
                valid_results,
                domain_url,
                primary_profile,
                site_context,
            )
            aggregated['prompt_analysis'] = PromptGapAnalyzer().analyze(
                valid_results,
                domain_url,
                primary_profile,
                max_prompts=24,
                use_llm=bool(self.options.get('llm_prompt_eval')),
                positioning=aggregated['positioning_analysis'],
                site_context=site_context,
            )
            if self.options.get('external_aeo_validation'):
                if self.tracker and self.job_id:
                    self.tracker.update(
                        self.job_id,
                        status="external",
                        current_step="Validating with external AEOs...",
                        pages_audited=len(page_results),
                        total_urls=len(page_results),
                        message="Asking generated questions to configured answer engines",
                    )
                from reporting.external_aeo_validator import ExternalAEOValidator

                aggregated['external_aeo_analysis'] = ExternalAEOValidator(
                    providers=self.options.get('external_aeo_providers'),
                    max_questions=self.options.get('external_aeo_max_questions'),
                ).validate(aggregated, site_context)
        except Exception as e:
            logger.warning(f"Failed to generate prompt gap analysis: {e}")
            aggregated['prompt_analysis'] = {}
            aggregated['positioning_analysis'] = {}

        return aggregated
