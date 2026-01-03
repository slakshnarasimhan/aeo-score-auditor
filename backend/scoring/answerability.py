"""
Answerability scoring (30 points max)
Calibrated: January 2026 - More flexible pattern matching
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
        """Score direct answer presence (max 12 points) - MORE FLEXIBLE"""
        score = 0
        
        # Check explicit answer patterns (original logic)
        answer_patterns = page_data.get('answer_patterns', [])
        answer_blocks = len([a for a in answer_patterns if a.get('type') != 'blockquote'])
        score += min(6, answer_blocks * 2)
        
        # NEW: Check for prose answers in first paragraphs
        paragraphs = page_data.get('paragraphs', [])
        if paragraphs:
            first_p = paragraphs[0]
            word_count = first_p.get('word_count', 0)
            
            # Good intro paragraph (common in Wikipedia, MDN, etc.)
            if 50 <= word_count <= 200:
                score += 4  # Strong intro
            elif 20 <= word_count < 50:
                score += 2  # Short intro
            elif word_count > 0:
                score += 1  # Something there
        
        # NEW: Credit for having substantial content at all
        total_word_count = page_data.get('word_count', 0)
        if total_word_count >= 500:
            score += 2  # Comprehensive content likely has answers
        
        logger.debug(f"Direct answers: {answer_blocks} blocks + prose = {score}/12 points")
        return min(12, score)
    
    def _score_questions(self, page_data: Dict) -> float:
        """Score question coverage (max 8 points) - MORE FLEXIBLE"""
        score = 0
        
        # Explicit questions with "?" (original logic)
        questions = page_data.get('questions', [])
        question_count = len(questions)
        score += min(4, (question_count / 10) * 8)
        
        # NEW: Count H2/H3 headings as implicit questions
        headings = page_data.get('headings', [])
        h2_h3_count = len([h for h in headings if h.get('level') in [2, 3]])
        
        # H2/H3 often answer implicit questions (especially in docs, encyclopedias)
        if h2_h3_count >= 10:
            score += 4
        elif h2_h3_count >= 6:
            score += 3
        elif h2_h3_count >= 3:
            score += 2
        elif h2_h3_count >= 1:
            score += 1
        
        logger.debug(f"Questions: {question_count} explicit + {h2_h3_count} headings = {score}/8 points")
        return min(8, score)
    
    def _score_conciseness(self, page_data: Dict) -> float:
        """Score answer conciseness (max 6 points) - MORE GENEROUS"""
        score = 0
        
        # Check for TL;DR
        answer_patterns = page_data.get('answer_patterns', [])
        has_tldr = any(a.get('type') == 'tldr' for a in answer_patterns)
        if has_tldr:
            score += 2
        
        # Check for bullet lists - MORE GENEROUS
        lists = page_data.get('lists', [])
        if len(lists) >= 5:
            score += 3
        elif len(lists) >= 3:
            score += 2
        elif len(lists) >= 1:
            score += 1
        
        # Check average paragraph length - MORE REALISTIC
        paragraphs = page_data.get('paragraphs', [])
        if paragraphs and len(paragraphs) >= 3:  # Need multiple paragraphs to judge
            avg_words = sum(p.get('word_count', 0) for p in paragraphs) / len(paragraphs)
            if avg_words <= 150:  # Increased from 100 - Wikipedia paragraphs are ~100-150 words
                score += 1
        
        logger.debug(f"Conciseness: TL;DR={has_tldr}, lists={len(lists)} = {score}/6 points")
        return min(6, score)
    
    def _score_formatting(self, page_data: Dict) -> float:
        """Score answer block formatting (max 4 points) - MORE FLEXIBLE"""
        score = 0
        
        # Check for proper heading structure (new)
        headings = page_data.get('headings', [])
        has_h1 = any(h.get('level') == 1 for h in headings)
        has_structure = len(headings) >= 3
        
        if has_h1 and has_structure:
            score += 2  # Well-structured content
        elif has_structure:
            score += 1
        
        # Check for emphasis tags
        paragraphs = page_data.get('paragraphs', [])
        emphasis_count = sum(1 for p in paragraphs if p.get('has_emphasis'))
        if emphasis_count >= 3:  # Lowered from 5
            score += 1
        
        # Check for answer patterns with specific formatting
        answer_patterns = page_data.get('answer_patterns', [])
        if any(a.get('type') in ['definition_box', 'callout', 'blockquote'] for a in answer_patterns):
            score += 1
        
        logger.debug(f"Formatting: structure={has_structure}, emphasis={emphasis_count} = {score}/4 points")
        return min(4, score)


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

