"""
Authority & Provenance scoring (15 points max)
"""
from typing import Dict
from loguru import logger


class AuthorityScorer:
    """Scores authority signals"""
    
    def __init__(self):
        self.max_score = 15
    
    def calculate(self, page_data: Dict) -> Dict:
        author_score = self._score_author(page_data)
        dates_score = self._score_dates(page_data)
        citations_score = self._score_citations(page_data)
        org_score = self._score_organization(page_data)
        
        total = author_score + dates_score + citations_score + org_score
        
        return {
            'score': round(total, 1),
            'max': self.max_score,
            'percentage': round((total / self.max_score) * 100, 1),
            'sub_scores': {
                'author_information': round(author_score, 1),
                'publication_date': round(dates_score, 1),
                'citations_sources': round(citations_score, 1),
                'organization_info': round(org_score, 1)
            }
        }
    
    def _score_author(self, page_data: Dict) -> float:
        """Score author information (max 5 points)"""
        author = page_data.get('author', {})
        if not author.get('found'):
            return 0
        
        score = 3  # Has author
        if 'jsonld' in author.get('sources', []):
            score += 2  # Structured author data
        
        return min(5, score)
    
    def _score_dates(self, page_data: Dict) -> float:
        """Score publication dates (max 3 points)"""
        dates = page_data.get('dates', {})
        score = 0
        
        if dates.get('published'):
            score += 2
        if dates.get('modified'):
            score += 1
        
        return score
    
    def _score_citations(self, page_data: Dict) -> float:
        """Score citations (max 4 points)"""
        external_links = page_data.get('external_links', [])
        count = len(external_links)
        
        return min(4, count * 0.5)
    
    def _score_organization(self, page_data: Dict) -> float:
        """Score organization info (max 3 points)"""
        schema_types = page_data.get('schema_types', [])
        if 'Organization' in schema_types:
            return 3
        return 0

