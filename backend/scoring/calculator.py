"""
Main scoring calculator with content-aware scoring profiles
"""
from typing import Dict
from loguru import logger

from .answerability import AnswerabilityScorer
from .structured_data import StructuredDataScorer
from .authority import AuthorityScorer
from .content_quality import ContentQualityScorer
from .citationability import CitationabilityScorer
from .technical import TechnicalScorer
from .content_profiles import get_profile


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
        Calculate complete AEO score with content-aware scoring
        
        Args:
            page_data: Extracted page data (dict or ExtractedPageData object)
            
        Returns:
            Complete score breakdown with content-aware weights applied
        """
        # Convert to dict if it's an object
        if hasattr(page_data, 'to_dict'):
            page_data = page_data.to_dict()
        
        logger.info(f"Calculating AEO score for {page_data.get('url', 'unknown')}")
        
        # Get content type and scoring profile
        content_classification = page_data.get('content_type', {})
        content_type = content_classification.get('type', 'informational')
        confidence = content_classification.get('confidence', 'low')
        profile = get_profile(content_type)
        
        logger.info(f"Content type: {content_type} (confidence: {confidence})")
        logger.info(f"Using scoring profile: {profile.name}")
        
        # Step 1: Calculate all raw scores
        raw_scores = {}
        for bucket_name, scorer in self.scorers.items():
            try:
                bucket_score = scorer.calculate(page_data)
                raw_scores[bucket_name] = bucket_score
            except Exception as e:
                logger.error(f"Error calculating {bucket_name}: {e}")
                raw_scores[bucket_name] = {'score': 0, 'max': scorer.max_score, 'error': str(e)}
        
        # Step 2: Calculate weighted max scores and normalization factor
        total_weighted_max = sum(
            raw_scores[bucket]['max'] * profile.get_weight(bucket)
            for bucket in self.scorers.keys()
        )
        
        # Normalization factor to maintain 95-point scale (leaving 5 for AI citation)
        normalization_factor = 95 / total_weighted_max if total_weighted_max > 0 else 1
        
        # Step 3: Apply weights - keep earned scores for low weights, give bonuses for high weights
        scores = {}
        for bucket_name in self.scorers.keys():
            bucket_score = raw_scores[bucket_name]
            weight = profile.get_weight(bucket_name)
            
            original_max = bucket_score['max']
            earned_score = bucket_score['score']
            
            # Calculate percentage earned
            percentage_earned = (earned_score / original_max) if original_max > 0 else 0
            
            if weight < 1.0:
                # For low-weight categories: Keep earned score as-is (don't penalize)
                # Only adjust the max to show it matters less
                rebalanced_max = original_max * weight * normalization_factor
                rebalanced_score = earned_score  # Keep the raw earned score
                
            elif weight > 1.0:
                # For high-weight categories: Give bonus for good performance
                rebalanced_max = original_max * weight * normalization_factor
                # Bonus: if percentage > 50%, apply weight as multiplier
                if percentage_earned > 0.5:
                    bonus_multiplier = 1 + (weight - 1) * percentage_earned
                    rebalanced_score = earned_score * bonus_multiplier
                else:
                    rebalanced_score = earned_score
                # Cap at max
                rebalanced_score = min(rebalanced_score, rebalanced_max)
                
            else:
                # Weight == 1.0: Standard scoring
                rebalanced_max = original_max * normalization_factor
                rebalanced_score = percentage_earned * rebalanced_max
            
            # Store results
            bucket_score['original_max'] = original_max
            bucket_score['original_score'] = earned_score
            bucket_score['score'] = round(rebalanced_score, 1)
            bucket_score['max'] = round(rebalanced_max, 1)
            bucket_score['weight_applied'] = weight
            bucket_score['percentage'] = round(percentage_earned * 100, 1)
            
            if weight != 1.0:
                logger.debug(f"{bucket_name}: {earned_score:.1f}/{original_max} ({percentage_earned*100:.0f}%) → {rebalanced_score:.1f}/{rebalanced_max:.1f} (weight: {weight}x)")
            else:
                logger.debug(f"{bucket_name}: {earned_score:.1f}/{original_max} → {rebalanced_score:.1f}/{rebalanced_max:.1f}")
            
            scores[bucket_name] = bucket_score
        
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
            'breakdown': scores,
            'content_classification': {
                'type': content_type,
                'confidence': confidence,
                'profile_used': profile.name,
                'description': content_classification.get('description', '')
            }
        }
        
        logger.info(f"Final score: {overall_score} ({grade}) - Content type: {content_type}")
        
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

