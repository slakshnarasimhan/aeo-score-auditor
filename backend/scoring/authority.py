"""
Authority & Provenance scoring (18 points max - increased from 15)
Calibrated: January 2026
"""
from typing import Dict
from loguru import logger
from urllib.parse import urlparse


class AuthorityScorer:
    """Scores authority signals"""
    
    def __init__(self):
        self.max_score = 18  # Increased from 15
        
        # Trusted domains with high authority
        self.trusted_domains = {
            'wikipedia.org', 'stackoverflow.com', 'github.com',
            'mozilla.org', 'w3.org', 'ietf.org',
            'mayoclinic.org', 'nih.gov', 'cdc.gov',
            'nytimes.com', 'bbc.com', 'reuters.com',
            'nature.com', 'science.org', 'pubmed.ncbi.nlm.nih.gov',
            'developer.android.com', 'docs.microsoft.com', 'cloud.google.com'
        }
    
    def calculate(self, page_data: Dict) -> Dict:
        domain_trust_score = self._score_domain_trust(page_data)
        author_score = self._score_author(page_data)
        dates_score = self._score_dates(page_data)
        citations_score = self._score_citations(page_data)
        security_score = self._score_security(page_data)
        
        total = domain_trust_score + author_score + dates_score + citations_score + security_score
        
        return {
            'score': round(total, 1),
            'max': self.max_score,
            'percentage': round((total / self.max_score) * 100, 1),
            'sub_scores': {
                'domain_trust': round(domain_trust_score, 1),
                'author_information': round(author_score, 1),
                'publication_date': round(dates_score, 1),
                'citations_sources': round(citations_score, 1),
                'security_https': round(security_score, 1)
            }
        }
    
    def _score_domain_trust(self, page_data: Dict) -> float:
        """Score domain authority (max 5 points) - NEW"""
        url = page_data.get('url', '')
        
        try:
            domain = urlparse(url).netloc.lower()
            # Remove www. prefix
            domain = domain.replace('www.', '')
            
            # Check if domain is in trusted list
            if any(trusted in domain for trusted in self.trusted_domains):
                return 5
            
            # Check for government/edu domains
            if domain.endswith('.gov') or domain.endswith('.edu'):
                return 4
            
            # Check for organization domains
            if domain.endswith('.org'):
                return 2
            
            return 0
        except:
            return 0
    
    def _score_author(self, page_data: Dict) -> float:
        """Score author information (max 4 points) - reduced from 5, not critical"""
        author = page_data.get('author', {})
        if not author.get('found'):
            return 0
        
        score = 3  # Has author
        if 'jsonld' in author.get('sources', []):
            score += 1  # Structured author data bonus
        
        return min(4, score)
    
    def _score_dates(self, page_data: Dict) -> float:
        """Score publication dates (max 4 points) - increased from 3"""
        dates = page_data.get('dates', {})
        score = 0
        
        # Either published OR modified counts
        if dates.get('published') or dates.get('modified'):
            score += 3  # Increased from 2
        
        # Bonus if both present
        if dates.get('published') and dates.get('modified'):
            score += 1
        
        return min(4, score)
    
    def _score_citations(self, page_data: Dict) -> float:
        """Score citations (max 3 points) - reduced from 4"""
        external_links = page_data.get('external_links', [])
        count = len(external_links)
        
        # More generous: 1 point per citation, max 3
        if count >= 5:
            return 3
        elif count >= 3:
            return 2
        elif count >= 1:
            return 1
        
        return 0
    
    def _score_security(self, page_data: Dict) -> float:
        """Score HTTPS and security (max 2 points) - NEW, replaces organization"""
        url = page_data.get('url', '')
        score = 0
        
        # HTTPS is critical for trust
        if url.startswith('https://'):
            score += 2
        
        return score

