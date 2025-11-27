"""
Technical & UX scoring (10 points max)
"""
from typing import Dict
from loguru import logger


class TechnicalScorer:
    """Scores technical SEO and UX signals"""
    
    def __init__(self):
        self.max_score = 10
    
    def calculate(self, page_data: Dict) -> Dict:
        performance_score = self._score_performance(page_data)
        mobile_score = self._score_mobile(page_data)
        semantic_score = self._score_semantic_html(page_data)
        linking_score = self._score_internal_linking(page_data)
        meta_score = self._score_meta_description(page_data)
        
        total = performance_score + mobile_score + semantic_score + linking_score + meta_score
        
        return {
            'score': round(total, 1),
            'max': self.max_score,
            'percentage': round((total / self.max_score) * 100, 1),
            'sub_scores': {
                'page_performance': round(performance_score, 1),
                'mobile_friendliness': round(mobile_score, 1),
                'semantic_html': round(semantic_score, 1),
                'internal_linking': round(linking_score, 1),
                'meta_description': round(meta_score, 1)
            }
        }
    
    def _score_performance(self, page_data: Dict) -> float:
        """Score page performance (max 3 points)"""
        performance = page_data.get('performance', {})
        ttfb = performance.get('ttfb', 0)
        
        # Simple scoring based on TTFB (in milliseconds)
        if ttfb <= 500:
            return 3
        elif ttfb <= 1000:
            return 2
        elif ttfb <= 2000:
            return 1
        else:
            return 0
    
    def _score_mobile(self, page_data: Dict) -> float:
        """Score mobile friendliness (max 2 points)"""
        # Simplified: check for viewport meta tag
        features = page_data.get('features', {})
        if features.get('has_meta_description'):  # Proxy for having meta tags
            return 2
        return 0
    
    def _score_semantic_html(self, page_data: Dict) -> float:
        """Score semantic HTML (max 2 points)"""
        # Check for proper heading hierarchy
        headings = page_data.get('headings', [])
        has_h1 = any(h['level'] == 1 for h in headings)
        has_h2 = any(h['level'] == 2 for h in headings)
        
        score = 0
        if has_h1:
            score += 1
        if has_h2:
            score += 1
        
        return score
    
    def _score_internal_linking(self, page_data: Dict) -> float:
        """Score internal linking (max 2 points)"""
        # Placeholder - would need to analyze internal links
        return 1
    
    def _score_meta_description(self, page_data: Dict) -> float:
        """Score meta description (max 1 point)"""
        meta_desc = page_data.get('meta_description', '')
        
        if meta_desc and 50 <= len(meta_desc) <= 160:
            return 1
        
        return 0

