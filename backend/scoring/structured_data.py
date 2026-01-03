"""
Structured Data scoring (15 points max)
Calibrated: January 2026 - More realistic expectations
"""
from typing import Dict
from loguru import logger


class StructuredDataScorer:
    """Scores structured data implementation"""
    
    def __init__(self):
        self.max_score = 15  # Reduced from 20 - was overweighted
    
    def calculate(self, page_data: Dict) -> Dict:
        """
        Calculate structured data score
        
        Breakdown:
        - Basic Schema Presence: 5 points (any schema at all)
        - Schema Quality: 5 points (relevance and completeness)
        - Advanced Features: 3 points (FAQ, breadcrumbs, etc.)
        - Open Graph/Twitter Cards: 2 points (common on good sites)
        """
        basic_score = self._score_basic_presence(page_data)
        quality_score = self._score_schema_quality(page_data)
        advanced_score = self._score_advanced_features(page_data)
        social_score = self._score_social_metadata(page_data)
        
        total = basic_score + quality_score + advanced_score + social_score
        
        return {
            'score': round(total, 1),
            'max': self.max_score,
            'percentage': round((total / self.max_score) * 100, 1),
            'sub_scores': {
                'basic_presence': round(basic_score, 1),
                'schema_quality': round(quality_score, 1),
                'advanced_features': round(advanced_score, 1),
                'social_metadata': round(social_score, 1)
            }
        }
    
    def _score_basic_presence(self, page_data: Dict) -> float:
        """Score basic schema presence (max 5 points) - ANY metadata is good"""
        score = 0
        
        # JSON-LD blocks (most common)
        jsonld = page_data.get('jsonld', [])
        valid_jsonld = [b for b in jsonld if 'error' not in b]
        if len(valid_jsonld) >= 1:
            score += 3  # Having ANY valid schema is a big win
            logger.debug(f"Found {len(valid_jsonld)} JSON-LD blocks → +3")
        
        # Microdata or RDFa (less common but still good)
        microdata = page_data.get('microdata', [])
        if len(microdata) >= 1:
            score += 2
            logger.debug(f"Found {len(microdata)} microdata → +2")
        
        # Open Graph (very common, should be present)
        og_tags = page_data.get('og_tags', {})
        if og_tags.get('title') or og_tags.get('description'):
            score += 2
            logger.debug(f"Found OG tags → +2")
        
        # NEW: Fallback for sites without schema but good basic meta
        if score == 0:
            # Check for basic HTML meta tags (title, description)
            title = page_data.get('title', '')
            meta_desc = page_data.get('meta_description', '')
            
            if title and len(title) > 10:  # Has a real title
                score += 1
                logger.debug(f"Has title → +1")
            
            if meta_desc and len(meta_desc) > 30:  # Has a real description
                score += 1
                logger.debug(f"Has meta description → +1")
            
            # Credit for having ANY headings (shows structure)
            headings = page_data.get('headings', [])
            if len(headings) >= 5:
                score += 1
                logger.debug(f"Has {len(headings)} headings → +1")
        
        logger.debug(f"Basic schema total: {score}/5 points")
        return min(5, score)
    
    def _score_schema_quality(self, page_data: Dict) -> float:
        """Score schema quality (max 5 points)"""
        score = 0
        
        # Schema types present
        schema_types = page_data.get('schema_types', [])
        
        # Core types (should have at least one)
        core_types = ['Article', 'BlogPosting', 'NewsArticle', 'WebPage', 
                     'Person', 'Organization', 'WebSite']
        has_core = any(t in schema_types for t in core_types)
        if has_core:
            score += 3
        
        # Rich types (FAQ, HowTo, etc.)
        rich_types = ['FAQPage', 'HowTo', 'QAPage', 'BreadcrumbList']
        has_rich = any(t in schema_types for t in rich_types)
        if has_rich:
            score += 2
        
        # Completeness check (if available)
        schema_validation = page_data.get('schema_validation', [])
        if schema_validation:
            completeness_scores = [v.get('completeness', 0) for v in schema_validation]
            avg_completeness = sum(completeness_scores) / len(completeness_scores)
            if avg_completeness >= 0.7:  # 70% complete is good
                score += 2
            elif avg_completeness >= 0.5:
                score += 1
        
        logger.debug(f"Schema quality: core={has_core}, rich={has_rich} = {score}/5 points")
        return min(5, score)
    
    def _score_advanced_features(self, page_data: Dict) -> float:
        """Score advanced features (max 3 points)"""
        score = 0
        
        # FAQ schema
        faq_schema = page_data.get('faq_schema', {})
        if faq_schema.get('found'):
            valid_pairs = faq_schema.get('valid_pairs', 0)
            if valid_pairs >= 3:
                score += 2
            elif valid_pairs >= 1:
                score += 1
        
        # Breadcrumbs
        schema_types = page_data.get('schema_types', [])
        if 'BreadcrumbList' in schema_types:
            score += 1
        
        logger.debug(f"Advanced features: FAQ={faq_schema.get('found')}, breadcrumbs={'BreadcrumbList' in schema_types} = {score}/3 points")
        return min(3, score)
    
    def _score_social_metadata(self, page_data: Dict) -> float:
        """Score social media metadata (max 2 points) - Very common on good sites"""
        score = 0
        
        # Open Graph
        og_tags = page_data.get('og_tags', {})
        og_complete = all(k in og_tags for k in ['title', 'description', 'type'])
        if og_complete:
            score += 1
        elif og_tags:
            score += 0.5
        
        # Twitter Cards
        twitter_card = page_data.get('twitter_card', {})
        if twitter_card.get('card'):
            score += 1
        
        logger.debug(f"Social metadata: OG={bool(og_tags)}, Twitter={bool(twitter_card)} = {score}/2 points")
        return min(2, score)

