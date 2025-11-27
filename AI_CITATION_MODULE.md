# AEO Score Auditor - AI-Citation Evaluation Module

## Overview
This module tests whether AI engines (GPT-4, Gemini, Perplexity, Claude) actually use and cite the target page when answering related questions. It provides deterministic, measurable evidence of AEO effectiveness.

---

## MODULE ARCHITECTURE

```
Page Content
    ↓
[1] Prompt Generator
    → Generate 20-100 targeted prompts
    ↓
[2] Multi-LLM Query Engine
    → Query GPT-4, Gemini, Perplexity, Claude
    → Collect responses + citations
    ↓
[3] Citation Detector
    → URL mention detection
    → Verbatim quote detection
    → Fact attribution detection
    ↓
[4] Semantic Similarity Analyzer
    → Embedding-based similarity
    → Answer alignment scoring
    ↓
[5] Evidence Aggregator
    → Compute AI-Citation Score
    → Store evidence snapshots
    ↓
Final Score + Evidence Report
```

---

## 1. PROMPT GENERATOR

### Purpose
Generate diverse, natural prompts that users would ask about the page topic.

### 1.1 Prompt Generation Strategy

```python
from typing import List, Dict
import random

class PromptGenerator:
    def __init__(self, page_data: ExtractedPageData):
        self.page_data = page_data
        self.topic = self.extract_main_topic()
        self.keywords = page_data.topics.get('main_keywords', [])
        self.questions = page_data.questions
    
    def generate_prompts(self, count: int = 20) -> List[Dict]:
        prompts = []
        
        # Strategy 1: Use existing questions from page (30%)
        prompts.extend(self.prompts_from_page_questions(int(count * 0.3)))
        
        # Strategy 2: Generate from keywords (30%)
        prompts.extend(self.prompts_from_keywords(int(count * 0.3)))
        
        # Strategy 3: Generate semantic variations (20%)
        prompts.extend(self.generate_semantic_variations(int(count * 0.2)))
        
        # Strategy 4: Generate related queries (20%)
        prompts.extend(self.generate_related_queries(int(count * 0.2)))
        
        return prompts[:count]
    
    def extract_main_topic(self) -> str:
        """Extract main topic from title and H1"""
        title = self.page_data.title
        headings = self.page_data.headings
        h1 = next((h['text'] for h in headings if h['level'] == 1), '')
        
        # Use title or H1 as main topic
        topic = h1 or title or 'this topic'
        return topic.strip()
```

---

### 1.2 Prompt Generation Methods

#### Method 1: From Page Questions

```python
def prompts_from_page_questions(self, count: int) -> List[Dict]:
    """Use questions already on the page"""
    prompts = []
    questions = self.page_data.questions[:count]
    
    for q in questions:
        prompts.append({
            'text': q['question'],
            'type': 'page_question',
            'source': 'extracted',
            'expected_answer': q.get('answer', '')[:200]
        })
    
    return prompts
```

---

#### Method 2: From Keywords

```python
QUESTION_TEMPLATES = {
    'what': [
        "What is {keyword}?",
        "What does {keyword} mean?",
        "What are the benefits of {keyword}?",
        "What is the purpose of {keyword}?",
    ],
    'how': [
        "How does {keyword} work?",
        "How to use {keyword}?",
        "How to implement {keyword}?",
        "How to get started with {keyword}?",
    ],
    'why': [
        "Why is {keyword} important?",
        "Why should I use {keyword}?",
        "Why does {keyword} matter?",
    ],
    'when': [
        "When to use {keyword}?",
        "When should I consider {keyword}?",
    ],
    'comparison': [
        "What is the difference between {keyword} and {related}?",
        "{keyword} vs {related}",
        "Compare {keyword} and {related}",
    ],
    'list': [
        "What are the best {keyword}?",
        "List of {keyword}",
        "Top {keyword} to consider",
    ]
}

def prompts_from_keywords(self, count: int) -> List[Dict]:
    """Generate questions using keyword templates"""
    prompts = []
    keywords = self.keywords[:10]
    
    for keyword in keywords:
        if len(prompts) >= count:
            break
        
        # Random question type
        q_type = random.choice(list(QUESTION_TEMPLATES.keys()))
        templates = QUESTION_TEMPLATES[q_type]
        template = random.choice(templates)
        
        # Fill template
        if '{related}' in template:
            related = random.choice([k for k in keywords if k != keyword])
            text = template.format(keyword=keyword, related=related)
        else:
            text = template.format(keyword=keyword)
        
        prompts.append({
            'text': text,
            'type': 'keyword_template',
            'keyword': keyword,
            'template_type': q_type
        })
    
    return prompts
```

---

#### Method 3: Semantic Variations

```python
def generate_semantic_variations(self, count: int) -> List[Dict]:
    """Generate variations of main questions"""
    prompts = []
    
    # Get top questions
    top_questions = self.questions[:5]
    
    variations = [
        "Explain {topic}",
        "Tell me about {topic}",
        "I need to understand {topic}",
        "Can you help me with {topic}?",
        "Looking for information on {topic}",
    ]
    
    for q in top_questions:
        if len(prompts) >= count:
            break
        
        # Extract topic from question
        topic = q['question'].replace('?', '').strip()
        
        variation = random.choice(variations).format(topic=topic.lower())
        prompts.append({
            'text': variation,
            'type': 'semantic_variation',
            'original': q['question']
        })
    
    return prompts
```

---

#### Method 4: Related Queries

```python
def generate_related_queries(self, count: int) -> List[Dict]:
    """Generate queries related to subtopics"""
    prompts = []
    
    # Use H2 headings as subtopics
    h2_headings = [h['text'] for h in self.page_data.headings if h['level'] == 2][:10]
    
    for heading in h2_headings:
        if len(prompts) >= count:
            break
        
        # Create query from heading
        if '?' not in heading:
            query = f"Tell me about {heading}"
        else:
            query = heading
        
        prompts.append({
            'text': query,
            'type': 'related_query',
            'source_heading': heading
        })
    
    return prompts
```

---

### 1.3 Prompt Enhancement

Add context and instructions to improve citation likelihood.

```python
def enhance_prompt(self, prompt_text: str, instruction_type: str = 'default') -> str:
    """Add instructions to encourage citations"""
    
    enhancements = {
        'default': prompt_text,
        
        'with_sources': f"{prompt_text}\n\nPlease provide sources for your answer.",
        
        'detailed': f"I need a detailed answer to: {prompt_text}\n\nInclude relevant sources and citations.",
        
        'web_search': f"{prompt_text}\n\nSearch the web for the most recent and authoritative information.",
        
        'compare': f"{prompt_text}\n\nCompare information from multiple sources."
    }
    
    return enhancements.get(instruction_type, prompt_text)
```

---

## 2. MULTI-LLM QUERY ENGINE

### Purpose
Query multiple AI engines and collect responses with citations.

### 2.1 LLM Client Factory

```python
from abc import ABC, abstractmethod
from typing import Optional
import asyncio

class LLMClient(ABC):
    @abstractmethod
    async def query(self, prompt: str) -> Dict:
        """Query the LLM and return response with citations"""
        pass

class GPT4Client(LLMClient):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model = "gpt-4-turbo"
    
    async def query(self, prompt: str) -> Dict:
        import openai
        openai.api_key = self.api_key
        
        try:
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant. Provide accurate information with sources when possible."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            return {
                'engine': 'gpt4',
                'prompt': prompt,
                'response': response.choices[0].message.content,
                'model': self.model,
                'finish_reason': response.choices[0].finish_reason,
                'citations': self.extract_citations_from_response(response.choices[0].message.content),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'engine': 'gpt4',
                'prompt': prompt,
                'error': str(e),
                'response': None
            }
    
    def extract_citations_from_response(self, text: str) -> List[str]:
        """Extract URLs from response text"""
        import re
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        return re.findall(url_pattern, text)

class GeminiClient(LLMClient):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model = "gemini-pro"
    
    async def query(self, prompt: str) -> Dict:
        import google.generativeai as genai
        genai.configure(api_key=self.api_key)
        
        try:
            model = genai.GenerativeModel(self.model)
            response = await model.generate_content_async(prompt)
            
            return {
                'engine': 'gemini',
                'prompt': prompt,
                'response': response.text,
                'model': self.model,
                'citations': self.extract_citations_from_response(response.text),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'engine': 'gemini',
                'prompt': prompt,
                'error': str(e),
                'response': None
            }
    
    def extract_citations_from_response(self, text: str) -> List[str]:
        import re
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        return re.findall(url_pattern, text)

class PerplexityClient(LLMClient):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model = "pplx-7b-online"
    
    async def query(self, prompt: str) -> Dict:
        import httpx
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    'https://api.perplexity.ai/chat/completions',
                    headers={
                        'Authorization': f'Bearer {self.api_key}',
                        'Content-Type': 'application/json'
                    },
                    json={
                        'model': self.model,
                        'messages': [
                            {'role': 'system', 'content': 'Be precise and concise. Provide sources.'},
                            {'role': 'user', 'content': prompt}
                        ]
                    },
                    timeout=30
                )
                
                data = response.json()
                response_text = data['choices'][0]['message']['content']
                
                # Perplexity often includes citations
                citations = data.get('citations', [])
                if not citations:
                    citations = self.extract_citations_from_response(response_text)
                
                return {
                    'engine': 'perplexity',
                    'prompt': prompt,
                    'response': response_text,
                    'model': self.model,
                    'citations': citations,
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            return {
                'engine': 'perplexity',
                'prompt': prompt,
                'error': str(e),
                'response': None
            }
    
    def extract_citations_from_response(self, text: str) -> List[str]:
        import re
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        return re.findall(url_pattern, text)

class ClaudeClient(LLMClient):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model = "claude-3-sonnet-20240229"
    
    async def query(self, prompt: str) -> Dict:
        import anthropic
        
        try:
            client = anthropic.AsyncAnthropic(api_key=self.api_key)
            
            response = await client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_text = response.content[0].text
            
            return {
                'engine': 'claude',
                'prompt': prompt,
                'response': response_text,
                'model': self.model,
                'citations': self.extract_citations_from_response(response_text),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'engine': 'claude',
                'prompt': prompt,
                'error': str(e),
                'response': None
            }
    
    def extract_citations_from_response(self, text: str) -> List[str]:
        import re
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        return re.findall(url_pattern, text)
```

---

### 2.2 Query Orchestrator

```python
class LLMQueryOrchestrator:
    def __init__(self, api_keys: Dict[str, str]):
        self.clients = {
            'gpt4': GPT4Client(api_keys.get('openai')),
            'gemini': GeminiClient(api_keys.get('google')),
            'perplexity': PerplexityClient(api_keys.get('perplexity')),
            'claude': ClaudeClient(api_keys.get('anthropic'))
        }
    
    async def query_all(self, prompts: List[Dict], engines: List[str] = None) -> List[Dict]:
        """Query multiple engines with multiple prompts"""
        if engines is None:
            engines = list(self.clients.keys())
        
        tasks = []
        for prompt_data in prompts:
            for engine in engines:
                if engine in self.clients:
                    task = self.query_single(
                        engine=engine,
                        prompt=prompt_data['text'],
                        prompt_metadata=prompt_data
                    )
                    tasks.append(task)
        
        # Execute all queries in parallel with rate limiting
        results = await self.execute_with_rate_limit(tasks, max_concurrent=10)
        return results
    
    async def query_single(self, engine: str, prompt: str, prompt_metadata: Dict) -> Dict:
        """Query a single engine"""
        client = self.clients[engine]
        result = await client.query(prompt)
        result['prompt_metadata'] = prompt_metadata
        return result
    
    async def execute_with_rate_limit(self, tasks: List, max_concurrent: int = 10) -> List:
        """Execute tasks with concurrency limit"""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def bounded_task(task):
            async with semaphore:
                return await task
        
        return await asyncio.gather(*[bounded_task(t) for t in tasks])
```

---

## 3. CITATION DETECTOR

### Purpose
Detect if the target page is cited or used in AI responses.

### 3.1 URL Citation Detection

```python
class CitationDetector:
    def __init__(self, target_url: str, target_domain: str):
        self.target_url = self.normalize_url(target_url)
        self.target_domain = target_domain
    
    def normalize_url(self, url: str) -> str:
        """Normalize URL for comparison"""
        url = url.lower().strip()
        url = url.rstrip('/')
        url = url.replace('http://', 'https://')
        url = url.replace('www.', '')
        return url
    
    def detect_url_citation(self, response: Dict) -> Dict:
        """Check if target URL appears in response or citations"""
        response_text = response.get('response', '')
        citations = response.get('citations', [])
        
        if not response_text:
            return {'found': False, 'method': None}
        
        # Method 1: Direct URL mention in text
        if self.target_url in response_text.lower():
            return {
                'found': True,
                'method': 'direct_url',
                'url': self.target_url
            }
        
        # Method 2: Domain mention
        if self.target_domain in response_text.lower():
            return {
                'found': True,
                'method': 'domain_mention',
                'domain': self.target_domain
            }
        
        # Method 3: In citations list
        for citation in citations:
            normalized_citation = self.normalize_url(citation)
            if self.target_domain in normalized_citation:
                return {
                    'found': True,
                    'method': 'citation_list',
                    'citation': citation
                }
        
        return {'found': False, 'method': None}
```

---

### 3.2 Verbatim Quote Detection

```python
from difflib import SequenceMatcher

class VerbatimDetector:
    def __init__(self, page_content: str):
        self.page_content = page_content
        self.sentences = self.split_into_sentences(page_content)
    
    def split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        import re
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if len(s.strip()) > 20]
    
    def detect_verbatim_quotes(self, response_text: str, min_length: int = 10) -> List[Dict]:
        """Find verbatim quotes from page in response"""
        quotes = []
        response_lower = response_text.lower()
        
        for sentence in self.sentences:
            sentence_lower = sentence.lower()
            
            # Check for exact matches
            if len(sentence) >= min_length and sentence_lower in response_lower:
                quotes.append({
                    'quote': sentence,
                    'match_type': 'exact',
                    'similarity': 1.0,
                    'length': len(sentence)
                })
                continue
            
            # Check for near-matches using fuzzy matching
            for response_sentence in self.split_into_sentences(response_text):
                similarity = SequenceMatcher(None, sentence_lower, response_sentence.lower()).ratio()
                if similarity > 0.9:  # 90% similar
                    quotes.append({
                        'quote': sentence,
                        'match_type': 'fuzzy',
                        'similarity': similarity,
                        'length': len(sentence),
                        'response_text': response_sentence
                    })
        
        return quotes
```

---

### 3.3 Fact Attribution Detection

```python
class FactAttributionDetector:
    def __init__(self, page_data: ExtractedPageData):
        self.page_data = page_data
        self.facts = self.extract_key_facts()
    
    def extract_key_facts(self) -> List[Dict]:
        """Extract key facts from page"""
        facts = []
        
        # Extract statistics
        import re
        stats_pattern = r'\b\d+(?:\.\d+)?%?\b'
        text = self.page_data.main_content
        
        for match in re.finditer(stats_pattern, text):
            context_start = max(0, match.start() - 50)
            context_end = min(len(text), match.end() + 50)
            context = text[context_start:context_end]
            
            facts.append({
                'type': 'statistic',
                'value': match.group(),
                'context': context
            })
        
        # Extract definitions (from answer patterns)
        for answer in self.page_data.answer_patterns:
            if answer['type'] == 'definition_box':
                facts.append({
                    'type': 'definition',
                    'text': answer['content']
                })
        
        # Extract list items (bullet points)
        for list_data in self.page_data.lists[:5]:  # Top 5 lists
            for item in list_data['items']:
                facts.append({
                    'type': 'list_item',
                    'text': item
                })
        
        return facts
    
    def detect_fact_usage(self, response_text: str) -> List[Dict]:
        """Check if response uses facts from page"""
        used_facts = []
        response_lower = response_text.lower()
        
        for fact in self.facts:
            if fact['type'] == 'statistic':
                # Check if statistic appears
                if fact['value'] in response_text:
                    used_facts.append({
                        'fact': fact,
                        'match_type': 'exact_statistic'
                    })
            
            elif fact['type'] in ['definition', 'list_item']:
                # Check for semantic similarity
                fact_text = fact['text'].lower()
                if len(fact_text) > 20 and fact_text in response_lower:
                    used_facts.append({
                        'fact': fact,
                        'match_type': 'content_match'
                    })
        
        return used_facts
```

---

## 4. SEMANTIC SIMILARITY ANALYZER

### Purpose
Measure how closely AI responses align with page content semantically.

### 4.1 Embedding-Based Similarity

```python
from sentence_transformers import SentenceTransformer, util
import numpy as np

class SemanticAnalyzer:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)
        self.cache = {}
    
    def get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for text with caching"""
        if text in self.cache:
            return self.cache[text]
        
        embedding = self.model.encode(text, convert_to_tensor=True)
        self.cache[text] = embedding
        return embedding
    
    def compute_similarity(self, text1: str, text2: str) -> float:
        """Compute cosine similarity between two texts"""
        emb1 = self.get_embedding(text1)
        emb2 = self.get_embedding(text2)
        
        similarity = util.cos_sim(emb1, emb2).item()
        return similarity
    
    def analyze_response_alignment(self, page_content: str, response: str) -> Dict:
        """Analyze how well response aligns with page content"""
        
        # Overall similarity
        overall_sim = self.compute_similarity(page_content, response)
        
        # Chunk-based analysis
        page_chunks = self.chunk_text(page_content, chunk_size=500)
        response_chunks = self.chunk_text(response, chunk_size=200)
        
        chunk_similarities = []
        for response_chunk in response_chunks:
            max_sim = 0
            for page_chunk in page_chunks:
                sim = self.compute_similarity(page_chunk, response_chunk)
                max_sim = max(max_sim, sim)
            chunk_similarities.append(max_sim)
        
        return {
            'overall_similarity': overall_sim,
            'avg_chunk_similarity': np.mean(chunk_similarities) if chunk_similarities else 0,
            'max_chunk_similarity': max(chunk_similarities) if chunk_similarities else 0,
            'min_chunk_similarity': min(chunk_similarities) if chunk_similarities else 0,
            'alignment_score': self.compute_alignment_score(overall_sim, chunk_similarities)
        }
    
    def chunk_text(self, text: str, chunk_size: int = 500) -> List[str]:
        """Split text into chunks"""
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size):
            chunk = ' '.join(words[i:i+chunk_size])
            chunks.append(chunk)
        return chunks
    
    def compute_alignment_score(self, overall_sim: float, chunk_sims: List[float]) -> float:
        """Compute weighted alignment score"""
        if not chunk_sims:
            return overall_sim
        
        # Weight: 60% overall, 40% average chunk similarity
        avg_chunk = np.mean(chunk_sims)
        return (overall_sim * 0.6) + (avg_chunk * 0.4)
```

---

### 4.2 Topic Overlap Analysis

```python
class TopicOverlapAnalyzer:
    def __init__(self):
        from sklearn.feature_extraction.text import TfidfVectorizer
        self.vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
    
    def analyze_topic_overlap(self, page_content: str, response: str) -> Dict:
        """Analyze topic/keyword overlap"""
        
        # Extract keywords using TF-IDF
        try:
            tfidf_matrix = self.vectorizer.fit_transform([page_content, response])
            feature_names = self.vectorizer.get_feature_names_out()
            
            page_scores = tfidf_matrix[0].toarray()[0]
            response_scores = tfidf_matrix[1].toarray()[0]
            
            # Get top keywords for each
            page_keywords = self.get_top_keywords(feature_names, page_scores, n=20)
            response_keywords = self.get_top_keywords(feature_names, response_scores, n=20)
            
            # Calculate overlap
            overlap = set(page_keywords) & set(response_keywords)
            overlap_ratio = len(overlap) / len(page_keywords) if page_keywords else 0
            
            return {
                'page_keywords': page_keywords,
                'response_keywords': response_keywords,
                'overlap_keywords': list(overlap),
                'overlap_ratio': overlap_ratio,
                'overlap_count': len(overlap)
            }
        except:
            return {
                'page_keywords': [],
                'response_keywords': [],
                'overlap_keywords': [],
                'overlap_ratio': 0,
                'overlap_count': 0
            }
    
    def get_top_keywords(self, feature_names: np.ndarray, scores: np.ndarray, n: int = 20) -> List[str]:
        """Get top N keywords by score"""
        indices = scores.argsort()[-n:][::-1]
        return [feature_names[i] for i in indices if scores[i] > 0]
```

---

## 5. EVIDENCE AGGREGATOR

### Purpose
Aggregate all detection results into final scores and evidence.

```python
class EvidenceAggregator:
    def __init__(self, target_url: str, page_data: ExtractedPageData):
        self.target_url = target_url
        self.target_domain = self.extract_domain(target_url)
        self.page_data = page_data
        
        # Initialize detectors
        self.citation_detector = CitationDetector(target_url, self.target_domain)
        self.verbatim_detector = VerbatimDetector(page_data.main_content)
        self.fact_detector = FactAttributionDetector(page_data)
        self.semantic_analyzer = SemanticAnalyzer()
        self.topic_analyzer = TopicOverlapAnalyzer()
    
    def extract_domain(self, url: str) -> str:
        from urllib.parse import urlparse
        return urlparse(url).netloc.replace('www.', '')
    
    def aggregate_results(self, llm_responses: List[Dict]) -> Dict:
        """Aggregate all detection results"""
        
        total_queries = len(llm_responses)
        successful_queries = [r for r in llm_responses if r.get('response')]
        
        # Citation metrics
        url_citations = 0
        domain_mentions = 0
        citation_list_mentions = 0
        
        # Content metrics
        verbatim_quotes_total = 0
        fact_usages_total = 0
        
        # Similarity metrics
        similarity_scores = []
        alignment_scores = []
        topic_overlaps = []
        
        # Evidence storage
        evidence = []
        
        for response in successful_queries:
            response_text = response.get('response', '')
            if not response_text:
                continue
            
            # 1. URL Citation Detection
            citation_result = self.citation_detector.detect_url_citation(response)
            if citation_result['found']:
                if citation_result['method'] == 'direct_url':
                    url_citations += 1
                elif citation_result['method'] == 'domain_mention':
                    domain_mentions += 1
                elif citation_result['method'] == 'citation_list':
                    citation_list_mentions += 1
                
                evidence.append({
                    'type': 'url_citation',
                    'response_id': response.get('timestamp'),
                    'engine': response.get('engine'),
                    'prompt': response.get('prompt'),
                    'citation_method': citation_result['method'],
                    'evidence': citation_result
                })
            
            # 2. Verbatim Quote Detection
            quotes = self.verbatim_detector.detect_verbatim_quotes(response_text)
            verbatim_quotes_total += len(quotes)
            
            if quotes:
                evidence.append({
                    'type': 'verbatim_quotes',
                    'response_id': response.get('timestamp'),
                    'engine': response.get('engine'),
                    'quote_count': len(quotes),
                    'quotes': quotes[:5]  # Store top 5
                })
            
            # 3. Fact Attribution
            facts_used = self.fact_detector.detect_fact_usage(response_text)
            fact_usages_total += len(facts_used)
            
            if facts_used:
                evidence.append({
                    'type': 'fact_usage',
                    'response_id': response.get('timestamp'),
                    'engine': response.get('engine'),
                    'fact_count': len(facts_used),
                    'facts': facts_used[:5]
                })
            
            # 4. Semantic Similarity
            semantic_result = self.semantic_analyzer.analyze_response_alignment(
                self.page_data.main_content,
                response_text
            )
            similarity_scores.append(semantic_result['overall_similarity'])
            alignment_scores.append(semantic_result['alignment_score'])
            
            # 5. Topic Overlap
            topic_result = self.topic_analyzer.analyze_topic_overlap(
                self.page_data.main_content,
                response_text
            )
            topic_overlaps.append(topic_result['overlap_ratio'])
        
        # Compute aggregate metrics
        citation_rate = (url_citations + domain_mentions + citation_list_mentions) / total_queries if total_queries > 0 else 0
        verbatim_rate = verbatim_quotes_total / len(successful_queries) if successful_queries else 0
        fact_usage_rate = fact_usages_total / len(successful_queries) if successful_queries else 0
        avg_similarity = np.mean(similarity_scores) if similarity_scores else 0
        avg_alignment = np.mean(alignment_scores) if alignment_scores else 0
        avg_topic_overlap = np.mean(topic_overlaps) if topic_overlaps else 0
        
        # Compute AI-Citation Score (0-5 points)
        ai_citation_score = self.compute_ai_citation_score(
            citation_rate=citation_rate,
            verbatim_rate=verbatim_rate,
            fact_usage_rate=fact_usage_rate,
            avg_similarity=avg_similarity,
            avg_alignment=avg_alignment
        )
        
        return {
            'ai_citation_score': ai_citation_score,
            'metrics': {
                'total_queries': total_queries,
                'successful_queries': len(successful_queries),
                'url_citations': url_citations,
                'domain_mentions': domain_mentions,
                'citation_list_mentions': citation_list_mentions,
                'citation_rate': citation_rate,
                'verbatim_quotes': verbatim_quotes_total,
                'verbatim_rate': verbatim_rate,
                'fact_usages': fact_usages_total,
                'fact_usage_rate': fact_usage_rate,
                'avg_similarity': avg_similarity,
                'avg_alignment': avg_alignment,
                'avg_topic_overlap': avg_topic_overlap
            },
            'evidence': evidence,
            'by_engine': self.aggregate_by_engine(llm_responses, evidence)
        }
    
    def compute_ai_citation_score(self, citation_rate: float, verbatim_rate: float, 
                                   fact_usage_rate: float, avg_similarity: float,
                                   avg_alignment: float) -> float:
        """
        Compute final AI-Citation Score (0-5 points)
        
        Components:
        - Direct Citation Rate (3 points max): URL/domain citations
        - Semantic Alignment (2 points max): How closely responses match page content
        """
        
        # Component 1: Citation Rate (3 points)
        # Scale: 0.1 citation rate = full 3 points
        citation_score = min(3.0, (citation_rate / 0.1) * 3.0)
        
        # Component 2: Semantic Alignment (2 points)
        alignment_score = avg_alignment * 2.0
        
        total_score = citation_score + alignment_score
        
        return round(total_score, 2)
    
    def aggregate_by_engine(self, responses: List[Dict], evidence: List[Dict]) -> Dict:
        """Break down results by engine"""
        by_engine = {}
        
        for response in responses:
            engine = response.get('engine', 'unknown')
            if engine not in by_engine:
                by_engine[engine] = {
                    'total_queries': 0,
                    'successful': 0,
                    'citations': 0,
                    'verbatim_quotes': 0,
                    'fact_usages': 0
                }
            
            by_engine[engine]['total_queries'] += 1
            if response.get('response'):
                by_engine[engine]['successful'] += 1
        
        # Add evidence counts
        for ev in evidence:
            engine = ev.get('engine', 'unknown')
            if engine in by_engine:
                if ev['type'] == 'url_citation':
                    by_engine[engine]['citations'] += 1
                elif ev['type'] == 'verbatim_quotes':
                    by_engine[engine]['verbatim_quotes'] += ev['quote_count']
                elif ev['type'] == 'fact_usage':
                    by_engine[engine]['fact_usages'] += ev['fact_count']
        
        return by_engine
```

---

## 6. COMPLETE AI-CITATION MODULE

### Main Orchestrator

```python
class AICitationModule:
    def __init__(self, api_keys: Dict[str, str]):
        self.prompt_generator = None
        self.query_orchestrator = LLMQueryOrchestrator(api_keys)
        self.evidence_aggregator = None
    
    async def evaluate(self, url: str, page_data: ExtractedPageData, 
                      prompt_count: int = 20, engines: List[str] = None) -> Dict:
        """
        Complete AI-Citation evaluation pipeline
        
        Steps:
        1. Generate prompts based on page content
        2. Query multiple LLMs with prompts
        3. Detect citations and content usage
        4. Compute semantic similarity
        5. Aggregate evidence and compute score
        """
        
        # Step 1: Generate prompts
        self.prompt_generator = PromptGenerator(page_data)
        prompts = self.prompt_generator.generate_prompts(count=prompt_count)
        
        # Step 2: Query LLMs
        llm_responses = await self.query_orchestrator.query_all(prompts, engines)
        
        # Step 3-5: Detect, analyze, aggregate
        self.evidence_aggregator = EvidenceAggregator(url, page_data)
        results = self.evidence_aggregator.aggregate_results(llm_responses)
        
        return {
            'url': url,
            'evaluated_at': datetime.now().isoformat(),
            'prompts_generated': len(prompts),
            'prompts': prompts,
            'llm_responses': llm_responses,
            **results
        }
```

---

## 7. USAGE EXAMPLE

```python
# Initialize module
api_keys = {
    'openai': 'sk-...',
    'google': 'AIza...',
    'perplexity': 'pplx-...',
    'anthropic': 'sk-ant-...'
}

ai_citation_module = AICitationModule(api_keys)

# Run evaluation
result = await ai_citation_module.evaluate(
    url='https://example.com/aeo-guide',
    page_data=extracted_page_data,
    prompt_count=20,
    engines=['gpt4', 'gemini', 'perplexity']
)

print(f"AI-Citation Score: {result['ai_citation_score']}/5")
print(f"Citation Rate: {result['metrics']['citation_rate']:.2%}")
print(f"Avg Similarity: {result['metrics']['avg_similarity']:.2f}")
```

---

## 8. OUTPUT FORMAT

```json
{
  "url": "https://example.com/page",
  "evaluated_at": "2024-11-26T10:00:00Z",
  "prompts_generated": 20,
  "ai_citation_score": 4.2,
  "metrics": {
    "total_queries": 60,
    "successful_queries": 58,
    "url_citations": 12,
    "domain_mentions": 8,
    "citation_rate": 0.333,
    "verbatim_quotes": 25,
    "verbatim_rate": 0.43,
    "fact_usages": 18,
    "avg_similarity": 0.72,
    "avg_alignment": 0.68
  },
  "evidence": [
    {
      "type": "url_citation",
      "engine": "perplexity",
      "citation_method": "citation_list",
      "evidence": {...}
    }
  ],
  "by_engine": {
    "gpt4": {"total_queries": 20, "citations": 3},
    "gemini": {"total_queries": 20, "citations": 5},
    "perplexity": {"total_queries": 20, "citations": 12}
  }
}
```

---

## NEXT STEPS
- Recommendation Engine (uses gaps identified here)
- API endpoints (to trigger evaluations)
- Evidence viewer UI (to show citation evidence)

