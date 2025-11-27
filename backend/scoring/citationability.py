"""
Citation-ability & Trust scoring (10 points max)
"""
from typing import Dict
from loguru import logger


class CitationabilityScorer:
    """Scores citation-ability signals"""
    
    def __init__(self):
        self.max_score = 10
    
    def calculate(self, page_data: Dict) -> Dict:
        facts_score = self._score_facts(page_data)
        data_score = self._score_data_tables(page_data)
        security_score = self._score_security(page_data)
        intrusive_score = self._score_no_intrusive(page_data)
        
        total = facts_score + data_score + security_score + intrusive_score
        
        return {
            'score': round(total, 1),
            'max': self.max_score,
            'percentage': round((total / self.max_score) * 100, 1),
            'sub_scores': {
                'clear_statements_of_fact': round(facts_score, 1),
                'data_tables_lists': round(data_score, 1),
                'https_security': round(security_score, 1),
                'no_intrusive_elements': round(intrusive_score, 1)
            }
        }
    
    def _score_facts(self, page_data: Dict) -> float:
        """Score clear facts (max 4 points)"""
        # Simplified: check for emphasis and structured content
        paragraphs = page_data.get('paragraphs', [])
        emphasized = sum(1 for p in paragraphs if p.get('has_emphasis'))
        
        return min(4, emphasized * 0.3)
    
    def _score_data_tables(self, page_data: Dict) -> float:
        """Score data tables and lists (max 3 points)"""
        tables = page_data.get('tables', [])
        lists = page_data.get('lists', [])
        
        score = min(1.5, len(tables) * 0.5) + min(1.5, len(lists) * 0.2)
        return min(3, score)
    
    def _score_security(self, page_data: Dict) -> float:
        """Score HTTPS (max 2 points)"""
        return 2 if page_data.get('is_https', False) else 0
    
    def _score_no_intrusive(self, page_data: Dict) -> float:
        """Score absence of intrusive elements (max 1 point)"""
        # Placeholder - would need to detect ads/popups
        return 1

