"""
Content Quality & Uniqueness scoring (10 points max)
"""
from typing import Dict
from loguru import logger
from datetime import datetime
from dateutil import parser as date_parser


class ContentQualityScorer:
    """Scores content quality"""
    
    def __init__(self):
        self.max_score = 10
    
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
        """Score content depth (max 4 points)"""
        word_count = page_data.get('word_count', 0)
        heading_count = len([h for h in page_data.get('headings', []) if h['level'] == 2])
        
        score = 0
        
        # Word count scoring
        if word_count >= 2000:
            score += 2
        elif word_count >= 1000:
            score += 1
        
        # Section count scoring
        if heading_count >= 8:
            score += 2
        elif heading_count >= 5:
            score += 1
        
        return score
    
    def _score_uniqueness(self, page_data: Dict) -> float:
        """Score unique value (max 3 points)"""
        tables = page_data.get('tables', [])
        lists = page_data.get('lists', [])
        
        score = 0
        
        if len(tables) >= 1:
            score += 1
        
        if len(lists) >= 3:
            score += 1
        
        # Placeholder for images/code
        score += 1
        
        return score
    
    def _score_freshness(self, page_data: Dict) -> float:
        """Score content freshness (max 3 points)"""
        dates = page_data.get('dates', {})
        last_modified = dates.get('modified') or dates.get('published')
        
        if not last_modified:
            return 0
        
        try:
            mod_date = date_parser.parse(last_modified)
            days_old = (datetime.now(mod_date.tzinfo) - mod_date).days
            
            if days_old <= 90:
                return 3
            elif days_old <= 180:
                return 2
            elif days_old <= 365:
                return 1
            else:
                return 0
        except:
            return 0

