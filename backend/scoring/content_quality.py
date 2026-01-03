"""
Content Quality & Uniqueness scoring (15 points max - increased from 10)
Calibrated: January 2026
"""
from typing import Dict
from loguru import logger
from datetime import datetime
from dateutil import parser as date_parser


class ContentQualityScorer:
    """Scores content quality"""
    
    def __init__(self):
        self.max_score = 15  # Increased from 10
    
    def calculate(self, page_data: Dict) -> Dict:
        depth_score = self._score_depth(page_data)
        unique_score = self._score_uniqueness(page_data)
        freshness_score = self._score_freshness(page_data)
        
        total = depth_score + unique_score + freshness_score
        
        return {
            'score': round(total, 1),
            'max': self.max_score,
            'percentage': round((total / self.max_score) * 100, 1),
            'sub_scores': {
                'content_depth': round(depth_score, 1),
                'unique_value_proposition': round(unique_score, 1),
                'freshness': round(freshness_score, 1)
            }
        }
    
    def _score_depth(self, page_data: Dict) -> float:
        """Score content depth (max 7 points) - increased from 4"""
        word_count = page_data.get('word_count', 0)
        heading_count = len([h for h in page_data.get('headings', []) if h['level'] == 2])
        
        score = 0
        
        # Word count scoring - LOWERED thresholds by 25%
        if word_count >= 1500:  # Was 2000
            score += 4  # Increased
        elif word_count >= 800:  # Was 1000
            score += 3
        elif word_count >= 400:  # New tier
            score += 2
        elif word_count >= 100:  # New tier
            score += 1
        
        # Section count scoring - more generous
        if heading_count >= 8:
            score += 3  # Increased from 2
        elif heading_count >= 5:
            score += 2  # Increased from 1
        elif heading_count >= 2:  # New tier
            score += 1
        
        return min(7, score)
    
    def _score_uniqueness(self, page_data: Dict) -> float:
        """Score unique value (max 4 points) - increased from 3"""
        tables = page_data.get('tables', [])
        lists = page_data.get('lists', [])
        
        score = 0
        
        # Tables are valuable
        if len(tables) >= 2:
            score += 2
        elif len(tables) >= 1:
            score += 1
        
        # Lists show structure
        if len(lists) >= 5:
            score += 2
        elif len(lists) >= 3:
            score += 1
        
        return min(4, score)
    
    def _score_freshness(self, page_data: Dict) -> float:
        """Score content freshness (max 4 points) - increased from 3"""
        dates = page_data.get('dates', {})
        last_modified = dates.get('modified') or dates.get('published')
        
        # If no date, give partial credit (content exists)
        if not last_modified:
            return 1  # Was 0 - too harsh
        
        try:
            mod_date = date_parser.parse(last_modified)
            days_old = (datetime.now(mod_date.tzinfo) - mod_date).days
            
            # More generous freshness scoring
            if days_old <= 90:
                return 4  # Increased from 3
            elif days_old <= 180:
                return 3  # Increased from 2
            elif days_old <= 365:
                return 2  # Increased from 1
            elif days_old <= 730:  # New: 2 years
                return 1
            else:
                return 0
        except:
            return 1  # Parse error, give some credit

