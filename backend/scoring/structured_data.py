"""
Structured Data scoring (20 points max)
"""
from typing import Dict
from loguru import logger


class StructuredDataScorer:
    """Scores structured data implementation"""
    
    def __init__(self):
        self.max_score = 20
    
    def calculate(self, page_data: Dict) -> Dict:
        """
        Calculate structured data score
        
        Breakdown:
        - JSON-LD Presence: 8 points
        - Schema Type Relevance: 6 points
        - FAQ Schema Quality: 4 points
        - Completeness: 2 points
        """
        jsonld_score = self._score_jsonld_presence(page_data)
        relevance_score = self._score_schema_relevance(page_data)
        faq_score = self._score_faq_schema(page_data)
        completeness_score = self._score_completeness(page_data)
        
        total = jsonld_score + relevance_score + faq_score + completeness_score
        
        return {
            'score': round(total, 1),
            'max': self.max_score,
            'percentage': round((total / self.max_score) * 100, 1),
            'sub_scores': {
                'jsonld_presence': round(jsonld_score, 1),
                'schema_type_relevance': round(relevance_score, 1),
                'faq_schema_quality': round(faq_score, 1),
                'completeness_of_required_fields': round(completeness_score, 1)
            }
        }
    
    def _score_jsonld_presence(self, page_data: Dict) -> float:
        """Score JSON-LD presence (max 8 points)"""
        jsonld = page_data.get('jsonld', [])
        valid_blocks = [b for b in jsonld if 'error' not in b]
        
        score = min(8, len(valid_blocks) * 2)
        logger.debug(f"JSON-LD presence: {len(valid_blocks)} blocks = {score}/8 points")
        return score
    
    def _score_schema_relevance(self, page_data: Dict) -> float:
        """Score schema type relevance (max 6 points)"""
        schema_types = page_data.get('schema_types', [])
        
        # Expected types for content pages
        relevant_types = ['Article', 'BlogPosting', 'NewsArticle', 'FAQPage', 
                         'HowTo', 'WebPage', 'Person', 'Organization']
        
        relevant_found = [t for t in schema_types if t in relevant_types]
        
        if not relevant_found:
            score = 0
        elif len(relevant_found) == 1:
            score = 3
        elif len(relevant_found) == 2:
            score = 5
        else:
            score = 6
        
        logger.debug(f"Schema relevance: {relevant_found} = {score}/6 points")
        return score
    
    def _score_faq_schema(self, page_data: Dict) -> float:
        """Score FAQ schema quality (max 4 points)"""
        faq_schema = page_data.get('faq_schema', {})
        
        if not faq_schema.get('found'):
            return 0
        
        valid_pairs = faq_schema.get('valid_pairs', 0)
        score = min(4, valid_pairs * 0.5)
        
        logger.debug(f"FAQ schema: {valid_pairs} Q&A pairs = {score}/4 points")
        return score
    
    def _score_completeness(self, page_data: Dict) -> float:
        """Score schema completeness (max 2 points)"""
        schema_validation = page_data.get('schema_validation', [])
        
        if not schema_validation:
            return 0
        
        completeness_scores = [v.get('completeness', 0) for v in schema_validation]
        avg_completeness = sum(completeness_scores) / len(completeness_scores)
        
        score = avg_completeness * 2
        logger.debug(f"Schema completeness: {avg_completeness:.2f} = {score}/2 points")
        return score

