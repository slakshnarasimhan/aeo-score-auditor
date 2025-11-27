"""
Semantic content extractor - questions, answers, topics
"""
import re
from typing import List, Dict
from bs4 import BeautifulSoup
from loguru import logger


class SemanticExtractor:
    """Extracts semantic meaning from content"""
    
    def __init__(self, soup: BeautifulSoup, main_content: str):
        self.soup = soup
        self.main_content = main_content
    
    def extract_questions(self) -> List[Dict]:
        """Extract questions from the page"""
        questions = []
        
        # Pattern 1: Question headings
        for heading in self.soup.find_all(['h2', 'h3', 'h4']):
            heading_text = heading.get_text(strip=True)
            if '?' in heading_text or self._is_question_pattern(heading_text):
                answer = self._extract_answer_after_heading(heading)
                questions.append({
                    'question': heading_text,
                    'type': 'heading',
                    'level': heading.name,
                    'answer': answer
                })
        
        # Pattern 2: Inline questions
        sentences = self.main_content.split('.')
        for sentence in sentences:
            if '?' in sentence and len(sentence.strip()) > 10:
                questions.append({
                    'question': sentence.strip(),
                    'type': 'inline',
                    'answer': None
                })
        
        logger.debug(f"Extracted {len(questions)} questions")
        return questions
    
    def _is_question_pattern(self, text: str) -> bool:
        """Check if text matches question patterns"""
        question_patterns = [
            r'^(How|What|Why|When|Where|Who|Which|Can|Is|Does|Do|Will|Should|Are)',
            r'(how to|what is|why does|when to)',
        ]
        return any(re.match(pattern, text, re.IGNORECASE) for pattern in question_patterns)
    
    def _extract_answer_after_heading(self, heading_elem) -> str:
        """Get text content immediately following a heading"""
        answer_parts = []
        current = heading_elem.find_next_sibling()
        
        # Collect paragraphs until next heading
        while current and current.name not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            if current.name in ['p', 'div']:
                text = current.get_text(strip=True)
                if len(text) > 20:
                    answer_parts.append(text)
            current = current.find_next_sibling()
            if len(answer_parts) >= 2:  # Limit to first 2 paragraphs
                break
        
        return ' '.join(answer_parts)[:500]  # Limit to 500 chars
    
    def extract_answer_patterns(self) -> List[Dict]:
        """Detect answer block patterns"""
        answers = []
        
        # Pattern 1: Definition/callout boxes
        for elem in self.soup.find_all(class_=lambda x: x and any(
            keyword in str(x).lower() for keyword in [
                'definition', 'callout', 'highlight', 'answer', 'tldr', 'summary'
            ]
        )):
            text = elem.get_text(strip=True)
            if len(text) > 20:
                answers.append({
                    'type': 'definition_box',
                    'content': text[:300],
                    'classes': elem.get('class', [])
                })
        
        # Pattern 2: TL;DR sections
        for elem in self.soup.find_all(['div', 'p', 'section']):
            text = elem.get_text(strip=True).lower()
            if any(text.startswith(prefix) for prefix in [
                'tldr', 'tl;dr', 'in short', 'quick answer', 'the answer is', 'summary:'
            ]):
                answers.append({
                    'type': 'tldr',
                    'content': elem.get_text(strip=True)[:300]
                })
        
        # Pattern 3: Blockquotes
        for quote in self.soup.find_all('blockquote'):
            text = quote.get_text(strip=True)
            if len(text) > 20:
                answers.append({
                    'type': 'blockquote',
                    'content': text[:300]
                })
        
        logger.debug(f"Extracted {len(answers)} answer patterns")
        return answers
    
    def extract_key_takeaways(self) -> List[str]:
        """Extract key takeaways or summary points"""
        takeaways = []
        
        keywords = ['key takeaway', 'main point', 'summary', 'conclusion', 'key insight']
        
        for elem in self.soup.find_all(['div', 'section', 'ul']):
            # Check if preceding heading contains keywords
            heading = elem.find_previous(['h2', 'h3'])
            if heading:
                heading_text = heading.get_text(strip=True).lower()
                if any(kw in heading_text for kw in keywords):
                    if elem.name in ['ul', 'ol']:
                        items = [li.get_text(strip=True) for li in elem.find_all('li')]
                        takeaways.extend(items[:5])  # Max 5 per list
                    else:
                        text = elem.get_text(strip=True)
                        if len(text) > 20:
                            takeaways.append(text[:200])
        
        logger.debug(f"Extracted {len(takeaways)} key takeaways")
        return takeaways[:10]  # Max 10 total
    
    def extract_topics(self) -> Dict:
        """Extract main topics and keywords"""
        # Simple keyword extraction based on frequency
        words = self.main_content.lower().split()
        
        # Common stop words to ignore
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                     'of', 'with', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                     'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
                     'can', 'could', 'may', 'might', 'must', 'this', 'that', 'these', 'those'}
        
        # Count word frequency
        word_freq = {}
        for word in words:
            # Clean word
            word = re.sub(r'[^\w]', '', word)
            if len(word) > 3 and word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get top keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        top_keywords = [word for word, count in sorted_words[:10]]
        
        return {
            'main_keywords': top_keywords,
            'keyword_density': {kw: word_freq.get(kw, 0) for kw in top_keywords[:5]},
            'total_words': len(words)
        }

