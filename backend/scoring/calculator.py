"""
Main scoring calculator
"""
from typing import Dict
from loguru import logger

from .answerability import AnswerabilityScorer
from .structured_data import StructuredDataScorer
from .authority import AuthorityScorer
from .content_quality import ContentQualityScorer
from .citationability import CitationabilityScorer
from .technical import TechnicalScorer


class AEOScoreCalculator:
    """Main scoring engine that orchestrates all scoring buckets"""
    
    def __init__(self):
        self.scorers = {
            'answerability': AnswerabilityScorer(),
            'structured_data': StructuredDataScorer(),
            'authority': AuthorityScorer(),
            'content_quality': ContentQualityScorer(),
            'citationability': CitationabilityScorer(),
            'technical': TechnicalScorer()
        }
    
    def calculate_score(self, page_data) -> Dict:
        """
        Calculate complete AEO score
        
        Args:
            page_data: Extracted page data (dict or ExtractedPageData object)
            
        Returns:
            Complete score breakdown
        """
        # Convert to dict if it's an object
        if hasattr(page_data, 'to_dict'):
            page_data = page_data.to_dict()
        
        logger.info(f"Calculating AEO score for {page_data.get('url', 'unknown')}")
        
        # Calculate each bucket
        scores = {}
        for bucket_name, scorer in self.scorers.items():
            try:
                bucket_score = scorer.calculate(page_data)
                scores[bucket_name] = bucket_score
                logger.debug(f"{bucket_name}: {bucket_score['score']}/{bucket_score['max']}")
            except Exception as e:
                logger.error(f"Error calculating {bucket_name}: {e}")
                scores[bucket_name] = {'score': 0, 'max': scorer.max_score, 'error': str(e)}
        
        # Add AI citation score if available
        if 'ai_citation_data' in page_data:
            ai_score = page_data['ai_citation_data'].get('ai_citation_score', 0)
            scores['ai_citation'] = {
                'score': ai_score,
                'max': 5,
                'percentage': (ai_score / 5) * 100
            }
        else:
            # No AI citation data
            scores['ai_citation'] = {
                'score': 0,
                'max': 5,
                'percentage': 0,
                'note': 'AI citation analysis not performed'
            }
        
        # Calculate overall score
        overall_score = sum(s['score'] for s in scores.values())
        grade = self._get_grade(overall_score)
        
        result = {
            'overall_score': round(overall_score, 1),
            'grade': grade,
            'breakdown': scores
        }
        
        logger.info(f"Final score: {overall_score} ({grade})")
        
        return result
    
    def _get_grade(self, score: float) -> str:
        """Convert score to letter grade"""
        if score >= 90: return 'A+'
        elif score >= 85: return 'A'
        elif score >= 80: return 'A-'
        elif score >= 75: return 'B+'
        elif score >= 70: return 'B'
        elif score >= 65: return 'B-'
        elif score >= 60: return 'C+'
        elif score >= 55: return 'C'
        elif score >= 50: return 'C-'
        else: return 'F'


# Example usage
if __name__ == "__main__":
    calculator = AEOScoreCalculator()
    
    # Sample data
    sample_data = {
        'url': 'https://example.com/page',
        'headings': [{'level': 1, 'text': 'Main Title'}],
        'questions': [],
        'answer_patterns': [],
        'jsonld': [],
        'word_count': 1500,
        'performance': {'lcp': 2000}
    }
    
    result = calculator.calculate_score(sample_data)
    print(result)

