# AEO Score Auditor - Data Extraction Specification

## Overview
This document defines the complete data extraction pipeline: what to extract, how to parse it, which techniques to use, and how to normalize the output.

---

## EXTRACTION PIPELINE ARCHITECTURE

```
URL Input
    ↓
[1] Page Fetcher (HTTP + Rendering)
    ↓
[2] Content Parser (DOM + Text)
    ↓
[3] Signal Extractors (Parallel Processing)
    ├── Structural Extractor
    ├── Semantic Extractor
    ├── Schema Extractor
    ├── Metadata Extractor
    ├── Performance Extractor
    └── Media Extractor
    ↓
[4] Feature Engineering
    ↓
[5] Normalized Data Model
    ↓
Scoring Engine
```

---

## 1. PAGE FETCHER

### Purpose
Fetch and render the page with full JavaScript execution.

### Implementation

**Technology**: Playwright or Puppeteer

**Process**:
```python
async def fetch_page(url: str) -> PageData:
    browser = await playwright.chromium.launch()
    page = await browser.new_page()
    
    # Set realistic user agent
    await page.set_extra_http_headers({
        'User-Agent': 'Mozilla/5.0 (compatible; AEOScoreBot/1.0)'
    })
    
    # Navigate with timeout
    await page.goto(url, wait_until='networkidle', timeout=30000)
    
    # Wait for dynamic content
    await page.wait_for_timeout(2000)
    
    # Collect data
    html_content = await page.content()
    final_url = page.url
    status_code = await page.evaluate('() => performance.navigation.redirectCount')
    
    # Performance metrics
    performance_metrics = await page.evaluate('''() => {
        const perf = performance.timing;
        const paint = performance.getEntriesByType('paint');
        return {
            ttfb: perf.responseStart - perf.requestStart,
            dom_load: perf.domContentLoadedEventEnd - perf.navigationStart,
            page_load: perf.loadEventEnd - perf.navigationStart,
            fcp: paint.find(p => p.name === 'first-contentful-paint')?.startTime || null,
        }
    }''')
    
    # Screenshot for debugging
    screenshot = await page.screenshot(type='png', full_page=False)
    
    await browser.close()
    
    return PageData(
        url=final_url,
        html=html_content,
        status_code=status_code,
        performance=performance_metrics,
        screenshot=screenshot
    )
```

**Output**:
- Raw HTML (with rendered JS)
- Final URL (after redirects)
- HTTP status code
- Performance timing metrics
- Screenshot

---

## 2. CONTENT PARSER

### Purpose
Parse HTML into structured DOM and extract clean text.

### Implementation

**Technology**: BeautifulSoup4 + lxml

```python
from bs4 import BeautifulSoup
import lxml

class ContentParser:
    def __init__(self, html: str):
        self.soup = BeautifulSoup(html, 'lxml')
        self.remove_noise()
    
    def remove_noise(self):
        """Remove non-content elements"""
        for element in self.soup.find_all(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            element.decompose()
        
        # Remove ads
        for element in self.soup.find_all(class_=lambda x: x and any(
            ad in str(x).lower() for ad in ['ad', 'advertisement', 'sponsored']
        )):
            element.decompose()
    
    def get_main_content(self) -> str:
        """Extract primary content area"""
        # Priority search for main content
        main = (
            self.soup.find('main') or
            self.soup.find('article') or
            self.soup.find('div', class_=lambda x: x and 'content' in str(x).lower()) or
            self.soup.find('body')
        )
        return main.get_text(separator=' ', strip=True) if main else ''
    
    def get_dom(self) -> BeautifulSoup:
        return self.soup
```

**Output**:
- Cleaned DOM tree
- Main content text
- Raw text with structure preserved

---

## 3. SIGNAL EXTRACTORS

### 3.1 STRUCTURAL EXTRACTOR

Extracts page structure and hierarchy.

#### 3.1.1 Heading Extraction

```python
def extract_headings(soup: BeautifulSoup) -> List[Heading]:
    headings = []
    for level in range(1, 7):
        for tag in soup.find_all(f'h{level}'):
            headings.append({
                'level': level,
                'text': tag.get_text(strip=True),
                'html': str(tag),
                'id': tag.get('id', ''),
                'classes': tag.get('class', [])
            })
    return headings
```

**Output**:
```json
[
  {
    "level": 1,
    "text": "Complete Guide to AEO",
    "html": "<h1>Complete Guide to AEO</h1>",
    "id": "main-title",
    "classes": ["page-title"]
  },
  {
    "level": 2,
    "text": "What is AEO?",
    "html": "<h2>What is AEO?</h2>",
    "id": "what-is-aeo",
    "classes": []
  }
]
```

---

#### 3.1.2 Paragraph & Block Extraction

```python
def extract_text_blocks(soup: BeautifulSoup) -> List[TextBlock]:
    blocks = []
    main_content = soup.find('main') or soup.find('article') or soup.find('body')
    
    for elem in main_content.find_all(['p', 'div', 'section'], recursive=True):
        text = elem.get_text(strip=True)
        if len(text) < 20:  # Skip tiny blocks
            continue
        
        blocks.append({
            'type': elem.name,
            'text': text,
            'word_count': len(text.split()),
            'has_emphasis': bool(elem.find(['strong', 'b', 'em', 'i'])),
            'classes': elem.get('class', []),
            'position': get_position_index(elem)
        })
    
    return blocks
```

---

#### 3.1.3 List Extraction

```python
def extract_lists(soup: BeautifulSoup) -> List[ListData]:
    lists = []
    for list_tag in soup.find_all(['ul', 'ol']):
        items = [li.get_text(strip=True) for li in list_tag.find_all('li', recursive=False)]
        if len(items) < 2:
            continue
        
        lists.append({
            'type': list_tag.name,
            'items': items,
            'item_count': len(items),
            'parent_section': get_parent_heading(list_tag)
        })
    
    return lists
```

**Output**:
```json
[
  {
    "type": "ul",
    "items": ["Item 1", "Item 2", "Item 3"],
    "item_count": 3,
    "parent_section": "Benefits of AEO"
  }
]
```

---

#### 3.1.4 Table Extraction

```python
def extract_tables(soup: BeautifulSoup) -> List[TableData]:
    tables = []
    for table in soup.find_all('table'):
        headers = [th.get_text(strip=True) for th in table.find_all('th')]
        rows = []
        
        for tr in table.find_all('tr'):
            cells = [td.get_text(strip=True) for td in tr.find_all('td')]
            if cells:
                rows.append(cells)
        
        if rows:
            tables.append({
                'headers': headers,
                'rows': rows,
                'row_count': len(rows),
                'col_count': len(headers) if headers else len(rows[0]),
                'caption': table.find('caption').get_text(strip=True) if table.find('caption') else ''
            })
    
    return tables
```

---

### 3.2 SEMANTIC EXTRACTOR

Extracts meaning, topics, and Q&A patterns.

#### 3.2.1 Question Detection

```python
import re

def extract_questions(soup: BeautifulSoup, text: str) -> List[Question]:
    questions = []
    
    # Pattern 1: Question headings
    for heading in soup.find_all(['h2', 'h3', 'h4']):
        heading_text = heading.get_text(strip=True)
        if '?' in heading_text or is_question_pattern(heading_text):
            questions.append({
                'question': heading_text,
                'type': 'heading',
                'level': heading.name,
                'answer': extract_answer_after_heading(heading)
            })
    
    # Pattern 2: Inline questions
    sentences = text.split('.')
    for sentence in sentences:
        if '?' in sentence:
            questions.append({
                'question': sentence.strip() + '?',
                'type': 'inline',
                'answer': None  # Would need NLP to extract
            })
    
    return questions

def is_question_pattern(text: str) -> bool:
    question_patterns = [
        r'^(How|What|Why|When|Where|Who|Which|Can|Is|Does|Do|Will|Should|Are)',
        r'(how to|what is|why does|when to)',
    ]
    return any(re.match(pattern, text, re.IGNORECASE) for pattern in question_patterns)

def extract_answer_after_heading(heading_elem) -> str:
    """Get text content immediately following a heading"""
    answer_parts = []
    current = heading_elem.find_next_sibling()
    
    # Collect paragraphs until next heading
    while current and current.name not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
        if current.name in ['p', 'div', 'ul', 'ol']:
            answer_parts.append(current.get_text(strip=True))
        current = current.find_next_sibling()
        if len(answer_parts) >= 3:  # Limit to first 3 elements
            break
    
    return ' '.join(answer_parts)[:500]  # Limit to 500 chars
```

**Output**:
```json
[
  {
    "question": "What is Answer Engine Optimization?",
    "type": "heading",
    "level": "h2",
    "answer": "Answer Engine Optimization (AEO) is the practice of optimizing content to appear as direct answers in AI-powered search engines and chatbots..."
  }
]
```

---

#### 3.2.2 Answer Pattern Detection

```python
def extract_answer_patterns(soup: BeautifulSoup) -> List[AnswerBlock]:
    answers = []
    
    # Pattern 1: Definition boxes
    for elem in soup.find_all(class_=lambda x: x and any(
        keyword in str(x).lower() for keyword in ['definition', 'callout', 'highlight', 'answer-box']
    )):
        answers.append({
            'type': 'definition_box',
            'content': elem.get_text(strip=True),
            'classes': elem.get('class', [])
        })
    
    # Pattern 2: TL;DR sections
    for elem in soup.find_all(['div', 'p', 'section']):
        text = elem.get_text(strip=True).lower()
        if text.startswith(('tldr', 'tl;dr', 'in short', 'quick answer', 'the answer is')):
            answers.append({
                'type': 'tldr',
                'content': elem.get_text(strip=True)
            })
    
    # Pattern 3: Blockquotes with answers
    for quote in soup.find_all('blockquote'):
        answers.append({
            'type': 'blockquote',
            'content': quote.get_text(strip=True)
        })
    
    return answers
```

---

#### 3.2.3 Key Takeaways Extraction

```python
def extract_key_takeaways(soup: BeautifulSoup) -> List[str]:
    takeaways = []
    
    # Look for "key takeaways" sections
    keywords = ['key takeaway', 'main point', 'summary', 'conclusion', 'key insight']
    for elem in soup.find_all(['div', 'section', 'ul']):
        heading = elem.find_previous(['h2', 'h3'])
        if heading:
            heading_text = heading.get_text(strip=True).lower()
            if any(kw in heading_text for kw in keywords):
                if elem.name in ['ul', 'ol']:
                    takeaways.extend([li.get_text(strip=True) for li in elem.find_all('li')])
                else:
                    takeaways.append(elem.get_text(strip=True))
    
    return takeaways[:10]  # Limit to 10
```

---

#### 3.2.4 Topic Modeling

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation

def extract_topics(text: str, n_topics: int = 5) -> List[Topic]:
    # Tokenize and vectorize
    vectorizer = TfidfVectorizer(
        max_features=1000,
        stop_words='english',
        ngram_range=(1, 2)
    )
    
    tfidf = vectorizer.fit_transform([text])
    feature_names = vectorizer.get_feature_names_out()
    
    # Get top keywords
    scores = tfidf.toarray()[0]
    top_indices = scores.argsort()[-20:][::-1]
    keywords = [feature_names[i] for i in top_indices if scores[i] > 0]
    
    return {
        'main_keywords': keywords[:10],
        'keyword_density': {kw: text.lower().count(kw) for kw in keywords[:5]},
        'total_words': len(text.split())
    }
```

---

### 3.3 SCHEMA EXTRACTOR

Extracts and validates structured data.

#### 3.3.1 JSON-LD Extraction

```python
import json

def extract_jsonld(soup: BeautifulSoup) -> List[dict]:
    jsonld_blocks = []
    
    for script in soup.find_all('script', type='application/ld+json'):
        try:
            data = json.loads(script.string)
            # Handle @graph arrays
            if isinstance(data, dict) and '@graph' in data:
                jsonld_blocks.extend(data['@graph'])
            elif isinstance(data, list):
                jsonld_blocks.extend(data)
            else:
                jsonld_blocks.append(data)
        except json.JSONDecodeError as e:
            jsonld_blocks.append({
                'error': 'Invalid JSON',
                'raw': script.string,
                'error_details': str(e)
            })
    
    return jsonld_blocks
```

**Output**:
```json
[
  {
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": "Complete Guide to AEO",
    "author": {
      "@type": "Person",
      "name": "John Doe"
    },
    "datePublished": "2024-01-15",
    "dateModified": "2024-11-20"
  }
]
```

---

#### 3.3.2 Schema Type Detection

```python
def detect_schema_types(jsonld_blocks: List[dict]) -> Dict[str, List[dict]]:
    schema_by_type = {}
    
    for block in jsonld_blocks:
        if 'error' in block:
            continue
        
        schema_type = block.get('@type', 'Unknown')
        if schema_type not in schema_by_type:
            schema_by_type[schema_type] = []
        schema_by_type[schema_type].append(block)
    
    return schema_by_type
```

---

#### 3.3.3 FAQ Schema Extraction

```python
def extract_faq_schema(jsonld_blocks: List[dict]) -> Dict:
    for block in jsonld_blocks:
        if block.get('@type') == 'FAQPage':
            qa_pairs = []
            for entity in block.get('mainEntity', []):
                question = entity.get('name', '')
                accepted_answer = entity.get('acceptedAnswer', {})
                answer = accepted_answer.get('text', '') if isinstance(accepted_answer, dict) else ''
                
                qa_pairs.append({
                    'question': question,
                    'answer': answer,
                    'valid': bool(question and answer)
                })
            
            return {
                'found': True,
                'qa_pairs': qa_pairs,
                'valid_pairs': sum(1 for qa in qa_pairs if qa['valid'])
            }
    
    return {'found': False, 'qa_pairs': [], 'valid_pairs': 0}
```

---

#### 3.3.4 Schema Validation

```python
REQUIRED_FIELDS = {
    'Article': ['headline', 'author', 'datePublished'],
    'Person': ['name'],
    'Organization': ['name'],
    'FAQPage': ['mainEntity'],
    'HowTo': ['name', 'step'],
    'Product': ['name', 'offers']
}

def validate_schema(schema_block: dict) -> Dict:
    schema_type = schema_block.get('@type')
    if not schema_type:
        return {'valid': False, 'reason': 'Missing @type'}
    
    required = REQUIRED_FIELDS.get(schema_type, [])
    present = [field for field in required if field in schema_block]
    missing = [field for field in required if field not in schema_block]
    
    return {
        'valid': len(missing) == 0,
        'schema_type': schema_type,
        'required_fields': required,
        'present_fields': present,
        'missing_fields': missing,
        'completeness': len(present) / len(required) if required else 1.0
    }
```

---

### 3.4 METADATA EXTRACTOR

Extracts page metadata and author information.

#### 3.4.1 Meta Tags Extraction

```python
def extract_meta_tags(soup: BeautifulSoup) -> Dict:
    meta_data = {}
    
    # Standard meta tags
    for meta in soup.find_all('meta'):
        name = meta.get('name') or meta.get('property')
        content = meta.get('content')
        if name and content:
            meta_data[name] = content
    
    # Title
    title_tag = soup.find('title')
    meta_data['title'] = title_tag.get_text(strip=True) if title_tag else ''
    
    # Canonical URL
    canonical = soup.find('link', rel='canonical')
    meta_data['canonical'] = canonical.get('href') if canonical else ''
    
    return meta_data
```

**Output**:
```json
{
  "title": "Complete Guide to AEO | SEO Blog",
  "description": "Learn everything about Answer Engine Optimization...",
  "keywords": "AEO, answer engine, optimization",
  "author": "John Doe",
  "og:title": "Complete Guide to AEO",
  "og:description": "Learn everything...",
  "og:image": "https://example.com/image.jpg",
  "article:published_time": "2024-01-15T10:00:00Z",
  "article:modified_time": "2024-11-20T14:30:00Z",
  "canonical": "https://example.com/aeo-guide"
}
```

---

#### 3.4.2 Author Detection

```python
def extract_author_info(soup: BeautifulSoup, jsonld_blocks: List[dict]) -> Dict:
    author_data = {
        'found': False,
        'sources': [],
        'name': None,
        'url': None,
        'image': None,
        'bio': None
    }
    
    # Source 1: JSON-LD
    for block in jsonld_blocks:
        if block.get('@type') in ['Article', 'BlogPosting', 'NewsArticle']:
            author = block.get('author')
            if author:
                author_data['found'] = True
                author_data['sources'].append('jsonld')
                if isinstance(author, dict):
                    author_data['name'] = author.get('name')
                    author_data['url'] = author.get('url')
                    author_data['image'] = author.get('image')
                elif isinstance(author, str):
                    author_data['name'] = author
    
    # Source 2: Meta tags
    meta_author = soup.find('meta', attrs={'name': 'author'})
    if meta_author and not author_data['name']:
        author_data['found'] = True
        author_data['sources'].append('meta')
        author_data['name'] = meta_author.get('content')
    
    # Source 3: Byline patterns
    byline_patterns = [
        soup.find(class_=lambda x: x and 'author' in str(x).lower()),
        soup.find(rel='author'),
        soup.find('span', string=lambda x: x and ('by ' in x.lower() or 'written by' in x.lower()))
    ]
    
    for elem in byline_patterns:
        if elem and not author_data['name']:
            author_data['found'] = True
            author_data['sources'].append('byline')
            text = elem.get_text(strip=True)
            author_data['name'] = re.sub(r'^(by|written by|author:)\s*', '', text, flags=re.IGNORECASE)
            break
    
    # Source 4: Author bio section
    bio_section = soup.find(class_=lambda x: x and any(kw in str(x).lower() for kw in ['author-bio', 'author-info', 'about-author']))
    if bio_section:
        author_data['bio'] = bio_section.get_text(strip=True)[:300]
    
    return author_data
```

---

#### 3.4.3 Date Extraction

```python
from dateutil import parser as date_parser

def extract_dates(soup: BeautifulSoup, jsonld_blocks: List[dict]) -> Dict:
    dates = {
        'published': None,
        'modified': None,
        'sources': []
    }
    
    # Source 1: JSON-LD
    for block in jsonld_blocks:
        if block.get('@type') in ['Article', 'BlogPosting', 'NewsArticle']:
            if 'datePublished' in block:
                dates['published'] = parse_date_safe(block['datePublished'])
                dates['sources'].append('jsonld')
            if 'dateModified' in block:
                dates['modified'] = parse_date_safe(block['dateModified'])
    
    # Source 2: Meta tags
    pub_meta = soup.find('meta', property='article:published_time')
    mod_meta = soup.find('meta', property='article:modified_time')
    
    if pub_meta and not dates['published']:
        dates['published'] = parse_date_safe(pub_meta.get('content'))
        dates['sources'].append('meta')
    
    if mod_meta and not dates['modified']:
        dates['modified'] = parse_date_safe(mod_meta.get('content'))
    
    # Source 3: Time tags
    time_tags = soup.find_all('time')
    for time_tag in time_tags:
        datetime_attr = time_tag.get('datetime')
        if datetime_attr and not dates['published']:
            dates['published'] = parse_date_safe(datetime_attr)
            dates['sources'].append('time_tag')
            break
    
    return dates

def parse_date_safe(date_string: str):
    try:
        return date_parser.parse(date_string).isoformat()
    except:
        return None
```

---

### 3.5 PERFORMANCE EXTRACTOR

Measures technical performance metrics.

#### 3.5.1 Core Web Vitals

```python
async def measure_core_web_vitals(page) -> Dict:
    vitals = await page.evaluate('''() => {
        return new Promise((resolve) => {
            let lcp = null;
            let fid = null;
            let cls = null;
            
            // LCP
            new PerformanceObserver((list) => {
                const entries = list.getEntries();
                lcp = entries[entries.length - 1].renderTime || entries[entries.length - 1].loadTime;
            }).observe({type: 'largest-contentful-paint', buffered: true});
            
            // FID
            new PerformanceObserver((list) => {
                const entries = list.getEntries();
                fid = entries[0].processingStart - entries[0].startTime;
            }).observe({type: 'first-input', buffered: true});
            
            // CLS
            let clsScore = 0;
            new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    if (!entry.hadRecentInput) {
                        clsScore += entry.value;
                    }
                }
                cls = clsScore;
            }).observe({type: 'layout-shift', buffered: true});
            
            setTimeout(() => resolve({lcp, fid, cls}), 5000);
        });
    }''')
    
    return vitals
```

---

#### 3.5.2 Page Size & Resources

```python
async def measure_page_resources(page) -> Dict:
    resources = await page.evaluate('''() => {
        const resources = performance.getEntriesByType('resource');
        const sizes = {
            scripts: 0,
            stylesheets: 0,
            images: 0,
            fonts: 0,
            total: 0,
            count: {
                scripts: 0,
                stylesheets: 0,
                images: 0,
                fonts: 0
            }
        };
        
        resources.forEach(resource => {
            const size = resource.transferSize || resource.encodedBodySize || 0;
            sizes.total += size;
            
            if (resource.initiatorType === 'script') {
                sizes.scripts += size;
                sizes.count.scripts++;
            } else if (resource.initiatorType === 'css') {
                sizes.stylesheets += size;
                sizes.count.stylesheets++;
            } else if (resource.initiatorType === 'img') {
                sizes.images += size;
                sizes.count.images++;
            } else if (resource.initiatorType === 'font' || resource.name.match(/\.(woff|woff2|ttf|eot)$/)) {
                sizes.fonts += size;
                sizes.count.fonts++;
            }
        });
        
        return sizes;
    }''')
    
    return resources
```

---

### 3.6 MEDIA EXTRACTOR

Extracts images and multimedia content.

```python
def extract_images(soup: BeautifulSoup) -> List[Dict]:
    images = []
    
    for img in soup.find_all('img'):
        src = img.get('src', '')
        alt = img.get('alt', '')
        
        # Skip tiny images (likely icons/tracking pixels)
        width = img.get('width', '')
        height = img.get('height', '')
        if width and height:
            try:
                if int(width) < 50 or int(height) < 50:
                    continue
            except:
                pass
        
        images.append({
            'src': src,
            'alt': alt,
            'width': width,
            'height': height,
            'loading': img.get('loading', 'eager'),
            'has_alt': bool(alt),
            'is_decorative': not alt or alt.lower() in ['image', 'photo', 'picture']
        })
    
    return images
```

---

## 4. FEATURE ENGINEERING

Transform raw extractions into scoring features.

```python
class FeatureEngineer:
    def __init__(self, extracted_data: Dict):
        self.data = extracted_data
    
    def compute_features(self) -> Dict:
        return {
            # Answerability features
            'answer_block_count': self.count_answer_blocks(),
            'question_count': self.count_questions(),
            'has_tldr': self.detect_tldr(),
            'avg_paragraph_length': self.compute_avg_paragraph_length(),
            
            # Structured data features
            'jsonld_block_count': len(self.data.get('jsonld', [])),
            'schema_types': self.get_schema_types(),
            'faq_qa_count': self.get_faq_count(),
            'schema_completeness': self.compute_schema_completeness(),
            
            # Authority features
            'has_author': self.data.get('author', {}).get('found', False),
            'has_publish_date': bool(self.data.get('dates', {}).get('published')),
            'external_link_count': self.count_external_links(),
            'citation_marker_count': self.count_citation_markers(),
            
            # Content quality features
            'word_count': self.data.get('topics', {}).get('total_words', 0),
            'heading_count': len(self.data.get('headings', [])),
            'table_count': len(self.data.get('tables', [])),
            'list_count': len(self.data.get('lists', [])),
            
            # Technical features
            'lcp_seconds': self.data.get('performance', {}).get('lcp', 0) / 1000,
            'has_viewport_meta': 'viewport' in self.data.get('meta', {}),
            'is_https': self.data.get('url', '').startswith('https://'),
            'has_meta_description': 'description' in self.data.get('meta', {}),
        }
    
    def count_answer_blocks(self) -> int:
        return len(self.data.get('answer_patterns', []))
    
    def count_questions(self) -> int:
        return len(self.data.get('questions', []))
    
    # ... other feature methods
```

---

## 5. NORMALIZED DATA MODEL

Final output format that feeds into the scoring engine.

```python
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime

@dataclass
class ExtractedPageData:
    # Metadata
    url: str
    fetched_at: datetime
    status_code: int
    
    # Content
    title: str
    meta_description: str
    main_content: str
    word_count: int
    
    # Structure
    headings: List[Dict]
    paragraphs: List[Dict]
    lists: List[Dict]
    tables: List[Dict]
    images: List[Dict]
    
    # Semantic
    questions: List[Dict]
    answer_patterns: List[Dict]
    key_takeaways: List[str]
    topics: Dict
    
    # Structured Data
    jsonld: List[Dict]
    schema_types: List[str]
    faq_schema: Dict
    schema_validation: List[Dict]
    
    # Authority
    author: Dict
    dates: Dict
    external_links: List[str]
    citations: int
    
    # Technical
    performance: Dict
    core_web_vitals: Dict
    resource_sizes: Dict
    is_mobile_friendly: bool
    is_https: bool
    
    # Features (computed)
    features: Dict
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)
```

---

## 6. EXTRACTION ORCHESTRATOR

Main coordinator that runs all extractors.

```python
class ExtractionPipeline:
    async def extract(self, url: str) -> ExtractedPageData:
        # Step 1: Fetch
        page_data = await self.fetch_page(url)
        
        # Step 2: Parse
        parser = ContentParser(page_data.html)
        soup = parser.get_dom()
        main_content = parser.get_main_content()
        
        # Step 3: Extract signals (parallel)
        extracted = await asyncio.gather(
            self.extract_structure(soup),
            self.extract_semantics(soup, main_content),
            self.extract_schema(soup),
            self.extract_metadata(soup, page_data),
            self.extract_performance(page_data),
            self.extract_media(soup)
        )
        
        # Step 4: Combine results
        combined = {
            'url': url,
            'fetched_at': datetime.now(),
            'status_code': page_data.status_code,
            **extracted[0],  # structure
            **extracted[1],  # semantics
            **extracted[2],  # schema
            **extracted[3],  # metadata
            **extracted[4],  # performance
            **extracted[5],  # media
        }
        
        # Step 5: Feature engineering
        engineer = FeatureEngineer(combined)
        combined['features'] = engineer.compute_features()
        
        # Step 6: Create normalized model
        return ExtractedPageData(**combined)
```

---

## 7. ERROR HANDLING & EDGE CASES

### 7.1 Common Issues

```python
class ExtractionError(Exception):
    pass

def handle_extraction_errors(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"Extraction error in {func.__name__}: {e}")
            return get_default_value(func)
    return wrapper

def get_default_value(func):
    """Return safe default based on function return type"""
    name = func.__name__
    if 'count' in name:
        return 0
    elif 'list' in name or 'extract' in name:
        return []
    elif 'dict' in name or 'data' in name:
        return {}
    else:
        return None
```

### 7.2 Graceful Degradation

- **JavaScript Required**: If JS fails, fall back to static HTML
- **Timeout**: Set 30s timeout, return partial data
- **Invalid Schema**: Mark as invalid but continue extraction
- **Missing Elements**: Use default values, never crash
- **Rate Limiting**: Implement exponential backoff

---

## 8. STORAGE FORMAT

Save extracted data for scoring and auditing.

```python
# MongoDB document structure
{
    "_id": "unique_page_id",
    "url": "https://example.com/page",
    "domain": "example.com",
    "extracted_at": "2024-11-26T10:00:00Z",
    "status": "success",
    "extraction_time_ms": 3500,
    
    "data": {
        # Full ExtractedPageData as nested document
    },
    
    "metadata": {
        "crawler_version": "1.0.0",
        "user_agent": "AEOScoreBot/1.0",
        "ip_address": "1.2.3.4"
    }
}
```

---

## NEXT STEPS

With data extraction defined, we can now build:
1. AI-Citation Evaluation Module (uses extracted content)
2. Scoring Engine (uses extracted features)
3. Recommendation Engine (uses gaps in extracted data)

