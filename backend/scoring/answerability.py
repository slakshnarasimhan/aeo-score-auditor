"""
Answerability scoring (30 points max)
"""
from typing import Dict
from loguru import logger


class AnswerabilityScorer:
    """Scores how well the page answers user questions"""
    
    def __init__(self):
        self.max_score = 30
    
    def calculate(self, page_data: Dict) -> Dict:
        """
        Calculate answerability score
        
        Breakdown:
        - Direct Answer Presence: 12 points
        - Question Coverage: 8 points
        - Answer Conciseness: 6 points
        - Answer Block Formatting: 4 points
        """
        # Sub-score 1: Direct Answer Presence
        direct_answer_score = self._score_direct_answers(page_data)
        
        # Sub-score 2: Question Coverage
        question_score = self._score_questions(page_data)
        
        # Sub-score 3: Answer Conciseness
        conciseness_score = self._score_conciseness(page_data)
        
        # Sub-score 4: Answer Block Formatting
        formatting_score = self._score_formatting(page_data)
        
        total = direct_answer_score + question_score + conciseness_score + formatting_score
        
        return {
            'score': round(total, 1),
            'max': self.max_score,
            'percentage': round((total / self.max_score) * 100, 1),
            'sub_scores': {
                'direct_answer_presence': round(direct_answer_score, 1),
                'question_coverage': round(question_score, 1),
                'answer_conciseness': round(conciseness_score, 1),
                'answer_block_formatting': round(formatting_score, 1)
            }
        }
    
    def _score_direct_answers(self, page_data: Dict) -> float:
        """Score direct answer presence (max 12 points)"""
        answer_patterns = page_data.get('answer_patterns', [])
        answer_blocks = len([a for a in answer_patterns if a.get('type') != 'blockquote'])
        
        # Formula: min(12, answer_blocks * 2)
        score = min(12, answer_blocks * 2)
        
        logger.debug(f"Direct answers: {answer_blocks} blocks = {score}/12 points")
        return score
    
    def _score_questions(self, page_data: Dict) -> float:
        """Score question coverage (max 8 points)"""
        questions = page_data.get('questions', [])
        question_count = len(questions)
        
        # Formula: min(8, (question_count / 10) * 8)
        coverage_ratio = question_count / 10
        score = min(8, coverage_ratio * 8)
        
        logger.debug(f"Questions: {question_count} = {score}/8 points")
        return score
    
    def _score_conciseness(self, page_data: Dict) -> float:
        """Score answer conciseness (max 6 points)"""
        score = 0
        
        # Check for TL;DR
        answer_patterns = page_data.get('answer_patterns', [])
        has_tldr = any(a.get('type') == 'tldr' for a in answer_patterns)
        if has_tldr:
            score += 2
        
        # Check for bullet lists
        lists = page_data.get('lists', [])
        if len(lists) >= 3:
            score += 2
        
        # Check average paragraph length
        paragraphs = page_data.get('paragraphs', [])
        if paragraphs:
            avg_words = sum(p.get('word_count', 0) for p in paragraphs) / len(paragraphs)
            if avg_words <= 100:
                score += 2
        
        logger.debug(f"Conciseness: TL;DR={has_tldr}, lists={len(lists)} = {score}/6 points")
        return score
    
    def _score_formatting(self, page_data: Dict) -> float:
        """Score answer block formatting (max 4 points)"""
        score = 0
        
        # Check for emphasis tags
        paragraphs = page_data.get('paragraphs', [])
        emphasis_count = sum(1 for p in paragraphs if p.get('has_emphasis'))
        if emphasis_count >= 5:
            score += 1
        
        # Check for answer patterns with specific formatting
        answer_patterns = page_data.get('answer_patterns', [])
        if any(a.get('type') in ['definition_box', 'callout'] for a in answer_patterns):
            score += 2
        
        # Check for blockquotes
        if any(a.get('type') == 'blockquote' for a in answer_patterns):
            score += 1
        
        logger.debug(f"Formatting: emphasis={emphasis_count}, patterns={len(answer_patterns)} = {score}/4 points")
        return score


# Example usage
if __name__ == "__main__":
    scorer = AnswerabilityScorer()
    
    sample_data = {
        'answer_patterns': [
            {'type': 'tldr', 'content': '...'},
            {'type': 'definition_box', 'content': '...'}
        ],
        'questions': [
            {'question': 'What is AEO?'},
            {'question': 'How does AEO work?'}
        ],
        'lists': [{'type': 'ul', 'items': ['a', 'b', 'c']}],
        'paragraphs': [
            {'word_count': 80, 'has_emphasis': True},
            {'word_count': 90, 'has_emphasis': True}
        ]
    }
    
    result = scorer.calculate(sample_data)
    print(result)

