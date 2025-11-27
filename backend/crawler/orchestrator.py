"""
Extraction orchestrator - coordinates all extractors
"""
from typing import Dict
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import os

from .parser import ContentParser
from .extractors.semantic import SemanticExtractor
from .extractors.schema import SchemaExtractor
from loguru import logger

# Use Playwright for JS-heavy sites if enabled (default: false for MVP speed)
USE_PLAYWRIGHT = os.getenv('USE_PLAYWRIGHT', 'false').lower() == 'true'

if USE_PLAYWRIGHT:
    try:
        from .fetcher import PageFetcher as Fetcher, PageData
        logger.info("Using Playwright fetcher (supports JavaScript rendering)")
    except ImportError as e:
        logger.warning(f"Playwright not available ({e}), falling back to HTTP fetcher")
        from .http_fetcher import HTTPFetcher as Fetcher, PageData
else:
    from .http_fetcher import HTTPFetcher as Fetcher, PageData
    logger.info("Using HTTP fetcher (fast, but no JavaScript support)")


@dataclass
class ExtractedPageData:
    """Complete extracted page data"""
    # Metadata
    url: str
    fetched_at: str
    status_code: int
    
    # Content
    title: str
    meta_description: str
    main_content: str
    word_count: int
    
    # Structure
    headings: list
    paragraphs: list
    lists: list
    tables: list
    images: list
    
    # Semantic
    questions: list
    answer_patterns: list
    key_takeaways: list
    topics: dict
    
    # Structured Data
    jsonld: list
    schema_types: list
    faq_schema: dict
    schema_validation: list
    
    # Authority
    author: dict
    dates: dict
    external_links: list
    
    # Technical
    performance: dict
    is_https: bool
    
    # Features (computed)
    features: dict
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)


class ExtractionOrchestrator:
    """Coordinates all extraction steps"""
    
    def __init__(self):
        self.fetcher = Fetcher()
    
    async def extract(self, url: str) -> ExtractedPageData:
        """
        Complete extraction pipeline
        
        Args:
            url: URL to extract data from
            
        Returns:
            ExtractedPageData with all extracted information
        """
        logger.info(f"Starting extraction for: {url}")
        
        # Step 1: Fetch page
        page_data = await self.fetcher.fetch(url)
        
        if page_data.error:
            logger.error(f"Failed to fetch {url}: {page_data.error}")
            raise Exception(f"Failed to fetch page: {page_data.error}")
        
        # Step 2: Parse HTML
        parser = ContentParser(page_data.html)
        soup = parser.get_dom()
        main_content = parser.get_main_content()
        
        # Step 3: Extract structure
        headings = parser.extract_headings()
        paragraphs = parser.extract_paragraphs()
        lists = parser.extract_lists()
        tables = parser.extract_tables()
        images = []  # Simplified for now
        
        # Step 4: Extract semantics
        semantic = SemanticExtractor(soup, main_content)
        questions = semantic.extract_questions()
        answer_patterns = semantic.extract_answer_patterns()
        key_takeaways = semantic.extract_key_takeaways()
        topics = semantic.extract_topics()
        
        # Step 5: Extract schema
        schema = SchemaExtractor(soup)
        jsonld = schema.extract_jsonld()
        schema_types = schema.detect_schema_types(jsonld)
        faq_schema = schema.extract_faq_schema(jsonld)
        schema_validation = schema.validate_all_schemas(jsonld)
        
        # Step 6: Extract metadata
        meta_tags = parser.extract_meta_tags()
        author = self._extract_author_info(soup, jsonld)
        dates = self._extract_dates(soup, jsonld)
        external_links = self._extract_external_links(soup, url)
        
        # Step 7: Compute features
        features = self._compute_features({
            'answer_patterns': answer_patterns,
            'questions': questions,
            'jsonld': jsonld,
            'author': author,
            'dates': dates,
            'external_links': external_links,
            'topics': topics,
            'headings': headings,
            'tables': tables,
            'lists': lists,
            'performance': page_data.performance,
            'url': url,
            'meta_tags': meta_tags
        })
        
        # Create final data object
        extracted = ExtractedPageData(
            url=url,
            fetched_at=datetime.utcnow().isoformat(),
            status_code=page_data.status_code,
            title=parser.get_title(),
            meta_description=meta_tags.get('description', ''),
            main_content=main_content,
            word_count=len(main_content.split()),
            headings=headings,
            paragraphs=paragraphs,
            lists=lists,
            tables=tables,
            images=images,
            questions=questions,
            answer_patterns=answer_patterns,
            key_takeaways=key_takeaways,
            topics=topics,
            jsonld=jsonld,
            schema_types=schema_types,
            faq_schema=faq_schema,
            schema_validation=schema_validation,
            author=author,
            dates=dates,
            external_links=external_links,
            performance=page_data.performance,
            is_https=url.startswith('https://'),
            features=features
        )
        
        logger.info(f"Extraction complete for: {url}")
        return extracted
    
    def _extract_author_info(self, soup, jsonld_blocks: list) -> dict:
        """Extract author information"""
        author_data = {'found': False, 'name': None, 'sources': []}
        
        # From JSON-LD
        for block in jsonld_blocks:
            if block.get('@type') in ['Article', 'BlogPosting', 'NewsArticle']:
                author = block.get('author')
                if author:
                    author_data['found'] = True
                    author_data['sources'].append('jsonld')
                    if isinstance(author, dict):
                        author_data['name'] = author.get('name')
                    elif isinstance(author, str):
                        author_data['name'] = author
                    break
        
        # From meta tags
        if not author_data['name']:
            meta_author = soup.find('meta', attrs={'name': 'author'})
            if meta_author:
                author_data['found'] = True
                author_data['sources'].append('meta')
                author_data['name'] = meta_author.get('content')
        
        return author_data
    
    def _extract_dates(self, soup, jsonld_blocks: list) -> dict:
        """Extract publication dates"""
        dates = {'published': None, 'modified': None, 'sources': []}
        
        # From JSON-LD
        for block in jsonld_blocks:
            if block.get('@type') in ['Article', 'BlogPosting', 'NewsArticle']:
                if 'datePublished' in block:
                    dates['published'] = block['datePublished']
                    dates['sources'].append('jsonld')
                if 'dateModified' in block:
                    dates['modified'] = block['dateModified']
                break
        
        return dates
    
    def _extract_external_links(self, soup, base_url: str) -> list:
        """Extract external links"""
        external_links = []
        base_domain = self._get_domain(base_url)
        
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href.startswith('http') and self._get_domain(href) != base_domain:
                external_links.append(href)
        
        return list(set(external_links))[:50]  # Max 50, unique
    
    def _get_domain(self, url: str) -> str:
        """Extract domain from URL"""
        from urllib.parse import urlparse
        return urlparse(url).netloc
    
    def _compute_features(self, data: dict) -> dict:
        """Compute features for scoring"""
        return {
            'answer_block_count': len(data.get('answer_patterns', [])),
            'question_count': len(data.get('questions', [])),
            'has_tldr': any(ap.get('type') == 'tldr' for ap in data.get('answer_patterns', [])),
            'jsonld_block_count': len(data.get('jsonld', [])),
            'has_author': data.get('author', {}).get('found', False),
            'has_publish_date': bool(data.get('dates', {}).get('published')),
            'external_link_count': len(data.get('external_links', [])),
            'word_count': data.get('topics', {}).get('total_words', 0),
            'heading_count': len(data.get('headings', [])),
            'table_count': len(data.get('tables', [])),
            'list_count': len(data.get('lists', [])),
            'is_https': data.get('url', '').startswith('https://'),
            'has_meta_description': bool(data.get('meta_tags', {}).get('description')),
        }

