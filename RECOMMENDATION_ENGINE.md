# AEO Score Auditor - Recommendation Engine

## Overview
The Recommendation Engine analyzes scoring gaps, detects missing elements, and generates actionable, prioritized fixes with code snippets, examples, and implementation guidance.

---

## ENGINE ARCHITECTURE

```
Extracted Page Data + Scores
    ↓
[1] Gap Analyzer
    → Identify what's missing or suboptimal
    ↓
[2] Recommendation Generator
    → Create specific, actionable fixes
    ↓
[3] Code Snippet Generator
    → Generate JSON-LD, HTML, content samples
    ↓
[4] Priority Scorer
    → Rank by Impact × Ease
    ↓
[5] Formatter & Grouper
    → Organize by category
    ↓
Prioritized Recommendation List
```

---

## 1. GAP ANALYZER

### Purpose
Identify specific deficiencies in each scoring bucket.

### 1.1 Gap Detection Framework

```python
from typing import List, Dict, Tuple
from dataclasses import dataclass

@dataclass
class Gap:
    category: str          # Which scoring bucket
    subcategory: str       # Specific area
    current_score: float   # Current points
    max_score: float       # Max possible points
    gap_size: float        # Points lost
    severity: str          # critical, high, medium, low
    description: str       # What's missing
    impact: float          # Potential score improvement (0-1)
    effort: float          # Implementation difficulty (0-1, 0=easy)
    
class GapAnalyzer:
    def __init__(self, page_data: ExtractedPageData, score_breakdown: Dict):
        self.page_data = page_data
        self.scores = score_breakdown
        self.gaps = []
    
    def analyze_all_gaps(self) -> List[Gap]:
        """Analyze gaps across all scoring categories"""
        self.gaps = []
        
        self.gaps.extend(self.analyze_answerability_gaps())
        self.gaps.extend(self.analyze_structured_data_gaps())
        self.gaps.extend(self.analyze_authority_gaps())
        self.gaps.extend(self.analyze_content_quality_gaps())
        self.gaps.extend(self.analyze_citationability_gaps())
        self.gaps.extend(self.analyze_technical_gaps())
        self.gaps.extend(self.analyze_ai_citation_gaps())
        
        return self.gaps
```

---

### 1.2 Answerability Gap Analysis

```python
def analyze_answerability_gaps(self) -> List[Gap]:
    gaps = []
    scores = self.scores['answerability']
    
    # Gap 1: Missing direct answers
    if scores['direct_answer_presence'] < 8:
        gaps.append(Gap(
            category='answerability',
            subcategory='direct_answer_presence',
            current_score=scores['direct_answer_presence'],
            max_score=12,
            gap_size=12 - scores['direct_answer_presence'],
            severity='high' if scores['direct_answer_presence'] < 4 else 'medium',
            description='Page lacks clear, direct answer blocks',
            impact=0.8,
            effort=0.3
        ))
    
    # Gap 2: Insufficient question coverage
    question_count = len(self.page_data.questions)
    if question_count < 5:
        gaps.append(Gap(
            category='answerability',
            subcategory='question_coverage',
            current_score=scores['question_coverage'],
            max_score=8,
            gap_size=8 - scores['question_coverage'],
            severity='high' if question_count < 2 else 'medium',
            description=f'Only {question_count} questions addressed, should have 8+',
            impact=0.7,
            effort=0.4
        ))
    
    # Gap 3: No TL;DR or summary
    has_tldr = any(ap['type'] == 'tldr' for ap in self.page_data.answer_patterns)
    if not has_tldr:
        gaps.append(Gap(
            category='answerability',
            subcategory='answer_conciseness',
            current_score=scores['answer_conciseness'],
            max_score=6,
            gap_size=2,
            severity='medium',
            description='Missing TL;DR or quick summary section',
            impact=0.6,
            effort=0.2
        ))
    
    # Gap 4: Poor text formatting
    if scores['answer_block_formatting'] < 3:
        gaps.append(Gap(
            category='answerability',
            subcategory='answer_block_formatting',
            current_score=scores['answer_block_formatting'],
            max_score=4,
            gap_size=4 - scores['answer_block_formatting'],
            severity='medium',
            description='Answers lack visual formatting (bold, callouts, highlights)',
            impact=0.5,
            effort=0.3
        ))
    
    return gaps
```

---

### 1.3 Structured Data Gap Analysis

```python
def analyze_structured_data_gaps(self) -> List[Gap]:
    gaps = []
    scores = self.scores['structured_data']
    
    # Gap 1: Missing JSON-LD
    jsonld_count = len(self.page_data.jsonld)
    if jsonld_count == 0:
        gaps.append(Gap(
            category='structured_data',
            subcategory='jsonld_presence',
            current_score=0,
            max_score=8,
            gap_size=8,
            severity='critical',
            description='No JSON-LD structured data found',
            impact=1.0,
            effort=0.4
        ))
    elif jsonld_count < 2:
        gaps.append(Gap(
            category='structured_data',
            subcategory='jsonld_presence',
            current_score=scores['jsonld_presence'],
            max_score=8,
            gap_size=8 - scores['jsonld_presence'],
            severity='high',
            description=f'Only {jsonld_count} JSON-LD block, should have 2-4+',
            impact=0.8,
            effort=0.4
        ))
    
    # Gap 2: Missing Article schema
    has_article = any(s.get('@type') in ['Article', 'BlogPosting', 'NewsArticle'] 
                     for s in self.page_data.jsonld)
    if not has_article and self.page_data.word_count > 500:
        gaps.append(Gap(
            category='structured_data',
            subcategory='schema_type_relevance',
            current_score=scores['schema_type_relevance'],
            max_score=6,
            gap_size=2,
            severity='high',
            description='Missing Article/BlogPosting schema for content page',
            impact=0.9,
            effort=0.3
        ))
    
    # Gap 3: No FAQ schema
    faq_qa_count = self.page_data.faq_schema.get('valid_pairs', 0)
    if faq_qa_count == 0 and len(self.page_data.questions) >= 3:
        gaps.append(Gap(
            category='structured_data',
            subcategory='faq_schema_quality',
            current_score=0,
            max_score=4,
            gap_size=4,
            severity='high',
            description='Missing FAQPage schema despite having Q&A content',
            impact=0.9,
            effort=0.5
        ))
    elif faq_qa_count < 5 and len(self.page_data.questions) >= 5:
        gaps.append(Gap(
            category='structured_data',
            subcategory='faq_schema_quality',
            current_score=scores['faq_schema_quality'],
            max_score=4,
            gap_size=4 - scores['faq_schema_quality'],
            severity='medium',
            description=f'FAQ schema has only {faq_qa_count} Q&A pairs, should have 5+',
            impact=0.7,
            effort=0.4
        ))
    
    # Gap 4: Incomplete schema fields
    if scores['completeness_of_required_fields'] < 1.5:
        gaps.append(Gap(
            category='structured_data',
            subcategory='completeness_of_required_fields',
            current_score=scores['completeness_of_required_fields'],
            max_score=2,
            gap_size=2 - scores['completeness_of_required_fields'],
            severity='medium',
            description='Schema blocks missing required fields',
            impact=0.6,
            effort=0.3
        ))
    
    return gaps
```

---

### 1.4 Authority Gap Analysis

```python
def analyze_authority_gaps(self) -> List[Gap]:
    gaps = []
    scores = self.scores['authority']
    
    # Gap 1: Missing author
    has_author = self.page_data.author.get('found', False)
    if not has_author:
        gaps.append(Gap(
            category='authority',
            subcategory='author_information',
            current_score=0,
            max_score=5,
            gap_size=5,
            severity='critical',
            description='No author information found',
            impact=0.9,
            effort=0.4
        ))
    elif scores['author_information'] < 4:
        gaps.append(Gap(
            category='authority',
            subcategory='author_information',
            current_score=scores['author_information'],
            max_score=5,
            gap_size=5 - scores['author_information'],
            severity='medium',
            description='Author info incomplete (missing schema, bio, or photo)',
            impact=0.7,
            effort=0.3
        ))
    
    # Gap 2: Missing dates
    has_published = bool(self.page_data.dates.get('published'))
    has_modified = bool(self.page_data.dates.get('modified'))
    
    if not has_published:
        gaps.append(Gap(
            category='authority',
            subcategory='publication_date',
            current_score=0,
            max_score=3,
            gap_size=3,
            severity='high',
            description='No publication date found',
            impact=0.8,
            effort=0.2
        ))
    
    if not has_modified:
        gaps.append(Gap(
            category='authority',
            subcategory='publication_date',
            current_score=scores['publication_date'],
            max_score=3,
            gap_size=1,
            severity='low',
            description='No last modified date',
            impact=0.4,
            effort=0.1
        ))
    
    # Gap 3: Few citations
    external_link_count = len(self.page_data.external_links)
    if external_link_count < 3:
        gaps.append(Gap(
            category='authority',
            subcategory='citations_sources',
            current_score=scores['citations_sources'],
            max_score=4,
            gap_size=4 - scores['citations_sources'],
            severity='medium',
            description=f'Only {external_link_count} external citations, should have 5+',
            impact=0.6,
            effort=0.5
        ))
    
    # Gap 4: No organization schema
    has_org = any(s.get('@type') == 'Organization' for s in self.page_data.jsonld)
    if not has_org:
        gaps.append(Gap(
            category='authority',
            subcategory='organization_info',
            current_score=scores['organization_info'],
            max_score=3,
            gap_size=3 - scores['organization_info'],
            severity='medium',
            description='Missing Organization schema',
            impact=0.6,
            effort=0.3
        ))
    
    return gaps
```

---

### 1.5 Additional Gap Analyzers

```python
def analyze_content_quality_gaps(self) -> List[Gap]:
    gaps = []
    scores = self.scores['content_quality']
    
    # Word count
    if self.page_data.word_count < 1000:
        gaps.append(Gap(
            category='content_quality',
            subcategory='content_depth',
            current_score=scores['content_depth'],
            max_score=4,
            gap_size=4 - scores['content_depth'],
            severity='high',
            description=f'Only {self.page_data.word_count} words, target 1500+',
            impact=0.7,
            effort=0.8
        ))
    
    # Missing data tables
    if len(self.page_data.tables) == 0:
        gaps.append(Gap(
            category='content_quality',
            subcategory='unique_value_proposition',
            current_score=scores['unique_value_proposition'],
            max_score=3,
            gap_size=1,
            severity='medium',
            description='No data tables or structured information',
            impact=0.5,
            effort=0.6
        ))
    
    # Outdated content
    days_old = self.calculate_days_since_update()
    if days_old > 180:
        gaps.append(Gap(
            category='content_quality',
            subcategory='freshness',
            current_score=scores['freshness'],
            max_score=3,
            gap_size=3 - scores['freshness'],
            severity='medium',
            description=f'Content is {days_old} days old, needs update',
            impact=0.6,
            effort=0.7
        ))
    
    return gaps

def analyze_citationability_gaps(self) -> List[Gap]:
    gaps = []
    scores = self.scores['citationability']
    
    # Missing HTTPS
    if not self.page_data.is_https:
        gaps.append(Gap(
            category='citationability',
            subcategory='security',
            current_score=0,
            max_score=2,
            gap_size=2,
            severity='critical',
            description='Site not using HTTPS',
            impact=0.9,
            effort=0.5
        ))
    
    return gaps

def analyze_technical_gaps(self) -> List[Gap]:
    gaps = []
    scores = self.scores['technical']
    
    # Poor performance
    lcp = self.page_data.performance.get('lcp', 0) / 1000
    if lcp > 4.0:
        gaps.append(Gap(
            category='technical',
            subcategory='page_performance',
            current_score=scores['page_performance'],
            max_score=3,
            gap_size=3 - scores['page_performance'],
            severity='high',
            description=f'LCP is {lcp:.1f}s, should be under 2.5s',
            impact=0.7,
            effort=0.8
        ))
    
    # No meta description
    if not self.page_data.meta_description:
        gaps.append(Gap(
            category='technical',
            subcategory='meta_description',
            current_score=0,
            max_score=1,
            gap_size=1,
            severity='medium',
            description='Missing meta description',
            impact=0.5,
            effort=0.1
        ))
    
    return gaps

def analyze_ai_citation_gaps(self) -> List[Gap]:
    gaps = []
    ai_score = self.scores.get('ai_citation', 0)
    
    if ai_score < 3:
        gaps.append(Gap(
            category='ai_citation',
            subcategory='citation_rate',
            current_score=ai_score,
            max_score=5,
            gap_size=5 - ai_score,
            severity='high',
            description='Low AI citation rate - content not being used by AI engines',
            impact=1.0,
            effort=0.6
        ))
    
    return gaps
```

---

## 2. RECOMMENDATION GENERATOR

### Purpose
Convert gaps into specific, actionable recommendations.

### 2.1 Recommendation Model

```python
@dataclass
class Recommendation:
    id: str
    title: str
    category: str
    subcategory: str
    priority: int               # 1-100
    impact: float               # Potential score gain
    effort: str                 # Easy, Medium, Hard
    severity: str               # critical, high, medium, low
    
    # Content
    description: str
    explanation: str
    how_to_fix: str
    
    # Evidence
    current_state: Dict
    desired_state: Dict
    
    # Code/Examples
    code_snippet: str           # JSON-LD or HTML
    before_example: str
    after_example: str
    
    # Metadata
    estimated_time: str         # "5 minutes", "1 hour"
    resources: List[str]        # Links to docs
    tags: List[str]

class RecommendationGenerator:
    def __init__(self, gaps: List[Gap], page_data: ExtractedPageData):
        self.gaps = gaps
        self.page_data = page_data
        self.recommendations = []
    
    def generate_all(self) -> List[Recommendation]:
        """Generate recommendations for all gaps"""
        for gap in self.gaps:
            rec = self.generate_recommendation(gap)
            if rec:
                self.recommendations.append(rec)
        
        # Sort by priority
        self.recommendations.sort(key=lambda r: r.priority, reverse=True)
        
        return self.recommendations
    
    def generate_recommendation(self, gap: Gap) -> Recommendation:
        """Route to specific generator based on gap type"""
        generator_map = {
            ('answerability', 'direct_answer_presence'): self.rec_add_answer_blocks,
            ('answerability', 'question_coverage'): self.rec_add_questions,
            ('answerability', 'answer_conciseness'): self.rec_add_tldr,
            ('answerability', 'answer_block_formatting'): self.rec_improve_formatting,
            
            ('structured_data', 'jsonld_presence'): self.rec_add_jsonld,
            ('structured_data', 'schema_type_relevance'): self.rec_add_article_schema,
            ('structured_data', 'faq_schema_quality'): self.rec_add_faq_schema,
            ('structured_data', 'completeness_of_required_fields'): self.rec_complete_schema,
            
            ('authority', 'author_information'): self.rec_add_author,
            ('authority', 'publication_date'): self.rec_add_dates,
            ('authority', 'citations_sources'): self.rec_add_citations,
            ('authority', 'organization_info'): self.rec_add_organization,
            
            ('content_quality', 'content_depth'): self.rec_expand_content,
            ('content_quality', 'unique_value_proposition'): self.rec_add_unique_value,
            ('content_quality', 'freshness'): self.rec_update_content,
            
            ('technical', 'page_performance'): self.rec_improve_performance,
            ('technical', 'meta_description'): self.rec_add_meta_description,
        }
        
        key = (gap.category, gap.subcategory)
        generator = generator_map.get(key)
        
        if generator:
            return generator(gap)
        
        return None
```

---

### 2.2 Recommendation Templates

#### Add Answer Blocks

```python
def rec_add_answer_blocks(self, gap: Gap) -> Recommendation:
    """Recommendation to add direct answer blocks"""
    
    # Detect potential questions from headings
    h2_headings = [h['text'] for h in self.page_data.headings if h['level'] == 2]
    suggested_questions = [h for h in h2_headings if '?' in h or self.is_question_pattern(h)]
    
    return Recommendation(
        id=f"rec_{gap.category}_{gap.subcategory}",
        title="Add Direct Answer Blocks",
        category=gap.category,
        subcategory=gap.subcategory,
        priority=self.calculate_priority(gap),
        impact=gap.impact,
        effort=self.map_effort(gap.effort),
        severity=gap.severity,
        
        description="Your page lacks clear, direct answer blocks that AI engines can easily extract.",
        
        explanation=(
            "AI engines prioritize content that directly answers user questions. "
            "Adding explicit answer blocks with clear formatting makes your content "
            "more likely to be cited and used in AI-generated responses."
        ),
        
        how_to_fix=(
            "1. Identify your main topic questions\n"
            "2. Add a dedicated answer section after each question\n"
            "3. Use formatting to highlight the answer (callout box, bold text)\n"
            "4. Keep answers concise (2-3 sentences) but complete\n"
            "5. Place answers prominently near the top of sections"
        ),
        
        current_state={
            'answer_blocks': len([ap for ap in self.page_data.answer_patterns if ap['type'] != 'blockquote']),
            'score': gap.current_score
        },
        
        desired_state={
            'answer_blocks': '6+',
            'target_score': gap.max_score
        },
        
        code_snippet=self.generate_answer_block_html(suggested_questions),
        
        before_example=(
            "What is AEO?\n\n"
            "Answer Engine Optimization involves various techniques and strategies..."
        ),
        
        after_example=(
            "What is AEO?\n\n"
            "**Quick Answer:** AEO (Answer Engine Optimization) is the practice of "
            "optimizing content to be directly used by AI-powered answer engines like "
            "ChatGPT, Perplexity, and Google SGE.\n\n"
            "[Followed by detailed explanation...]"
        ),
        
        estimated_time="30 minutes",
        resources=[
            "https://schema.org/Answer",
            "https://developers.google.com/search/docs/appearance/structured-data/qapage"
        ],
        tags=['content', 'formatting', 'high-impact']
    )

def generate_answer_block_html(self, questions: List[str]) -> str:
    """Generate HTML template for answer blocks"""
    example_q = questions[0] if questions else "Your Question Here"
    
    return f'''<!-- Add after each major heading -->
<div class="answer-block">
    <h2>{example_q}</h2>
    <div class="quick-answer">
        <strong>Quick Answer:</strong> 
        [Your concise, direct answer in 2-3 sentences]
    </div>
    <p>[Detailed explanation follows...]</p>
</div>

<!-- Suggested CSS -->
<style>
.answer-block {{
    margin: 2rem 0;
}}
.quick-answer {{
    background: #f0f7ff;
    border-left: 4px solid #0066cc;
    padding: 1rem;
    margin: 1rem 0;
    font-size: 1.1rem;
}}
</style>'''
```

---

#### Add FAQ Schema

```python
def rec_add_faq_schema(self, gap: Gap) -> Recommendation:
    """Recommendation to add FAQPage schema"""
    
    # Extract existing questions
    questions = self.page_data.questions[:8]  # Top 8
    
    return Recommendation(
        id=f"rec_{gap.category}_{gap.subcategory}",
        title="Implement FAQPage Structured Data",
        category=gap.category,
        subcategory=gap.subcategory,
        priority=self.calculate_priority(gap),
        impact=gap.impact,
        effort=self.map_effort(gap.effort),
        severity=gap.severity,
        
        description="Add FAQPage JSON-LD schema to help AI engines understand your Q&A content.",
        
        explanation=(
            "FAQPage schema explicitly marks question-answer pairs, making it trivial for "
            "AI engines to extract and cite your content. This is one of the highest-impact "
            "structured data types for AEO."
        ),
        
        how_to_fix=(
            "1. Identify all question-answer pairs on your page\n"
            "2. Copy the JSON-LD template below\n"
            "3. Replace example questions/answers with your content\n"
            "4. Add the script tag to your page's <head> or <body>\n"
            "5. Validate using Google's Rich Results Test"
        ),
        
        current_state={
            'faq_schema': 'Missing',
            'questions_on_page': len(questions),
            'score': gap.current_score
        },
        
        desired_state={
            'faq_schema': 'Implemented',
            'qa_pairs': '5-10',
            'target_score': gap.max_score
        },
        
        code_snippet=self.generate_faq_schema(questions),
        
        before_example="<!-- No structured data -->",
        
        after_example=self.generate_faq_schema(questions),
        
        estimated_time="20 minutes",
        resources=[
            "https://schema.org/FAQPage",
            "https://developers.google.com/search/docs/appearance/structured-data/faqpage",
            "https://validator.schema.org/"
        ],
        tags=['schema', 'json-ld', 'high-impact', 'quick-win']
    )

def generate_faq_schema(self, questions: List[Dict]) -> str:
    """Generate FAQPage JSON-LD"""
    qa_items = []
    
    for q in questions[:8]:  # Max 8 for example
        question_text = q.get('question', 'Example question?')
        answer_text = q.get('answer', 'Example answer text.')
        
        qa_items.append(f'''    {{
      "@type": "Question",
      "name": "{question_text}",
      "acceptedAnswer": {{
        "@type": "Answer",
        "text": "{answer_text[:200]}..."
      }}
    }}''')
    
    return f'''<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
{",\\n".join(qa_items)}
  ]
}}
</script>'''
```

---

#### Add Article Schema

```python
def rec_add_article_schema(self, gap: Gap) -> Recommendation:
    """Recommendation to add Article schema"""
    
    title = self.page_data.title
    author_name = self.page_data.author.get('name', 'Your Name')
    published = self.page_data.dates.get('published', '2024-01-01')
    
    return Recommendation(
        id=f"rec_{gap.category}_{gap.subcategory}",
        title="Add Article Schema with Author and Dates",
        category=gap.category,
        subcategory=gap.subcategory,
        priority=self.calculate_priority(gap),
        impact=gap.impact,
        effort=self.map_effort(gap.effort),
        severity=gap.severity,
        
        description="Implement Article structured data to establish authority and provenance.",
        
        explanation=(
            "Article schema tells AI engines who wrote the content, when it was published, "
            "and who published it. This establishes credibility and makes your content more "
            "trustworthy and cite-able."
        ),
        
        how_to_fix=(
            "1. Copy the JSON-LD template below\n"
            "2. Fill in your article details:\n"
            "   - headline (page title)\n"
            "   - author name and URL\n"
            "   - publication date\n"
            "   - modification date\n"
            "   - main image URL\n"
            "3. Add to your page <head> or <body>\n"
            "4. Validate with schema validator"
        ),
        
        current_state={
            'article_schema': 'Missing',
            'has_author': bool(author_name),
            'has_date': bool(published)
        },
        
        desired_state={
            'article_schema': 'Complete',
            'all_required_fields': 'Present'
        },
        
        code_snippet=self.generate_article_schema(title, author_name, published),
        
        before_example="<!-- No Article schema -->",
        after_example=self.generate_article_schema(title, author_name, published),
        
        estimated_time="15 minutes",
        resources=[
            "https://schema.org/Article",
            "https://developers.google.com/search/docs/appearance/structured-data/article"
        ],
        tags=['schema', 'authority', 'high-impact']
    )

def generate_article_schema(self, title: str, author: str, published: str) -> str:
    """Generate Article JSON-LD"""
    return f'''<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "{title}",
  "author": {{
    "@type": "Person",
    "name": "{author}",
    "url": "https://yoursite.com/about/{author.lower().replace(' ', '-')}"
  }},
  "publisher": {{
    "@type": "Organization",
    "name": "Your Site Name",
    "logo": {{
      "@type": "ImageObject",
      "url": "https://yoursite.com/logo.png"
    }}
  }},
  "datePublished": "{published}",
  "dateModified": "{datetime.now().date().isoformat()}",
  "image": "https://yoursite.com/article-image.jpg",
  "description": "Your article description"
}}
</script>'''
```

---

#### Add TL;DR Section

```python
def rec_add_tldr(self, gap: Gap) -> Recommendation:
    """Recommendation to add TL;DR summary"""
    
    # Generate sample TL;DR from first paragraphs
    first_para = self.page_data.paragraphs[0]['text'] if self.page_data.paragraphs else ''
    
    return Recommendation(
        id=f"rec_{gap.category}_{gap.subcategory}",
        title="Add TL;DR Summary Block",
        category=gap.category,
        subcategory=gap.subcategory,
        priority=self.calculate_priority(gap),
        impact=gap.impact,
        effort=self.map_effort(gap.effort),
        severity=gap.severity,
        
        description="Add a TL;DR (Too Long; Didn't Read) summary at the top of your article.",
        
        explanation=(
            "A TL;DR provides a scannable summary that AI engines can easily extract. "
            "This is especially valuable for long-form content, giving AI a concise answer "
            "to quote while still allowing deeper exploration."
        ),
        
        how_to_fix=(
            "1. Write a 2-4 sentence summary of your main points\n"
            "2. Place it prominently near the top (after intro)\n"
            "3. Use visual formatting to make it stand out\n"
            "4. Include key facts, numbers, or takeaways\n"
            "5. Label it clearly as 'TL;DR', 'Quick Summary', or 'Key Takeaways'"
        ),
        
        current_state={'tldr_section': 'Missing'},
        desired_state={'tldr_section': 'Present'},
        
        code_snippet='''<div class="tldr-box">
    <h2>TL;DR</h2>
    <p><strong>Key Points:</strong></p>
    <ul>
        <li>Main takeaway #1</li>
        <li>Main takeaway #2</li>
        <li>Main takeaway #3</li>
    </ul>
</div>

<style>
.tldr-box {
    background: #fffbf0;
    border: 2px solid #ffc107;
    border-radius: 8px;
    padding: 1.5rem;
    margin: 2rem 0;
}
.tldr-box h2 {
    margin-top: 0;
    color: #f57c00;
}
</style>''',
        
        before_example=first_para[:200] + "...",
        
        after_example=f'''**TL;DR:** [Concise 2-3 sentence summary of the entire article]

{first_para[:200]}...''',
        
        estimated_time="15 minutes",
        resources=[
            "https://www.nngroup.com/articles/blah-blah-text/",
            "Best practices for summary writing"
        ],
        tags=['content', 'formatting', 'quick-win']
    )
```

---

#### Add Author Information

```python
def rec_add_author(self, gap: Gap) -> Recommendation:
    """Recommendation to add author information"""
    
    return Recommendation(
        id=f"rec_{gap.category}_{gap.subcategory}",
        title="Add Complete Author Information",
        category=gap.category,
        subcategory=gap.subcategory,
        priority=self.calculate_priority(gap),
        impact=gap.impact,
        effort=self.map_effort(gap.effort),
        severity=gap.severity,
        
        description="Add visible author byline and structured author data.",
        
        explanation=(
            "Author information establishes E-E-A-T (Experience, Expertise, "
            "Authoritativeness, Trustworthiness). AI engines heavily weight content "
            "from known, credible authors."
        ),
        
        how_to_fix=(
            "1. Add author byline visible on page\n"
            "2. Include author photo (optional but recommended)\n"
            "3. Add Person schema within Article schema\n"
            "4. Link to author bio page\n"
            "5. Include credentials if relevant to topic"
        ),
        
        current_state={'author': 'Missing'},
        desired_state={'author': 'Complete with schema'},
        
        code_snippet='''<!-- Visible byline (add near title) -->
<div class="author-byline">
    <img src="/authors/john-doe.jpg" alt="John Doe" class="author-photo">
    <div class="author-info">
        <p class="author-name">By <a href="/about/john-doe">John Doe</a></p>
        <p class="author-title">Senior AEO Strategist</p>
    </div>
</div>

<!-- JSON-LD (add to Article schema) -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "author": {
    "@type": "Person",
    "name": "John Doe",
    "url": "https://yoursite.com/about/john-doe",
    "jobTitle": "Senior AEO Strategist",
    "image": "https://yoursite.com/authors/john-doe.jpg"
  }
}
</script>''',
        
        before_example="[Article content with no author]",
        after_example="By John Doe\nSenior AEO Strategist\n\n[Article content]",
        
        estimated_time="20 minutes",
        resources=[
            "https://schema.org/Person",
            "https://developers.google.com/search/docs/appearance/structured-data/article#author"
        ],
        tags=['authority', 'schema', 'high-impact']
    )
```

---

### 2.3 Priority Calculation

```python
def calculate_priority(self, gap: Gap) -> int:
    """
    Calculate priority score (1-100)
    
    Formula: Priority = (Impact × 50) + (Ease × 30) + (Severity × 20)
    where Ease = (1 - Effort)
    """
    # Severity multiplier
    severity_weight = {
        'critical': 1.0,
        'high': 0.8,
        'medium': 0.6,
        'low': 0.4
    }
    
    impact_score = gap.impact * 50
    ease_score = (1 - gap.effort) * 30
    severity_score = severity_weight.get(gap.severity, 0.5) * 20
    
    priority = impact_score + ease_score + severity_score
    
    return int(min(100, max(1, priority)))

def map_effort(self, effort_float: float) -> str:
    """Convert effort float to label"""
    if effort_float < 0.3:
        return "Easy"
    elif effort_float < 0.6:
        return "Medium"
    else:
        return "Hard"
```

---

## 3. RECOMMENDATION TEMPLATES LIBRARY

### Complete Template Catalog

```python
class RecommendationTemplates:
    """Library of all recommendation templates"""
    
    # Content Recommendations
    rec_add_answer_blocks = rec_add_answer_blocks
    rec_add_questions = lambda self, gap: self.generate_from_template('add_questions', gap)
    rec_add_tldr = rec_add_tldr
    rec_improve_formatting = lambda self, gap: self.generate_from_template('formatting', gap)
    rec_expand_content = lambda self, gap: self.generate_from_template('expand_content', gap)
    rec_add_unique_value = lambda self, gap: self.generate_from_template('unique_value', gap)
    rec_update_content = lambda self, gap: self.generate_from_template('update_content', gap)
    rec_add_citations = lambda self, gap: self.generate_from_template('citations', gap)
    
    # Schema Recommendations
    rec_add_jsonld = lambda self, gap: self.generate_from_template('basic_jsonld', gap)
    rec_add_article_schema = rec_add_article_schema
    rec_add_faq_schema = rec_add_faq_schema
    rec_add_organization = lambda self, gap: self.generate_from_template('organization', gap)
    rec_complete_schema = lambda self, gap: self.generate_from_template('complete_schema', gap)
    
    # Authority Recommendations
    rec_add_author = rec_add_author
    rec_add_dates = lambda self, gap: self.generate_from_template('dates', gap)
    
    # Technical Recommendations
    rec_improve_performance = lambda self, gap: self.generate_from_template('performance', gap)
    rec_add_meta_description = lambda self, gap: self.generate_from_template('meta_desc', gap)
```

---

## 4. OUTPUT FORMATTER

### Purpose
Format recommendations for display and export.

```python
class RecommendationFormatter:
    def __init__(self, recommendations: List[Recommendation]):
        self.recommendations = recommendations
    
    def format_for_ui(self) -> Dict:
        """Format for frontend display"""
        return {
            'total_recommendations': len(self.recommendations),
            'by_severity': self.group_by_severity(),
            'by_category': self.group_by_category(),
            'quick_wins': self.get_quick_wins(),
            'high_impact': self.get_high_impact(),
            'all_recommendations': [self.format_single(r) for r in self.recommendations]
        }
    
    def group_by_severity(self) -> Dict:
        grouped = {'critical': [], 'high': [], 'medium': [], 'low': []}
        for rec in self.recommendations:
            grouped[rec.severity].append(rec.id)
        return grouped
    
    def group_by_category(self) -> Dict:
        grouped = {}
        for rec in self.recommendations:
            if rec.category not in grouped:
                grouped[rec.category] = []
            grouped[rec.category].append(rec.id)
        return grouped
    
    def get_quick_wins(self) -> List[Dict]:
        """Get easy, high-impact recommendations"""
        quick_wins = [r for r in self.recommendations 
                      if r.effort == 'Easy' and r.impact >= 0.7]
        return [self.format_single(r) for r in quick_wins[:5]]
    
    def get_high_impact(self) -> List[Dict]:
        """Get highest impact recommendations"""
        high_impact = sorted(self.recommendations, key=lambda r: r.impact, reverse=True)
        return [self.format_single(r) for r in high_impact[:10]]
    
    def format_single(self, rec: Recommendation) -> Dict:
        """Format single recommendation"""
        return {
            'id': rec.id,
            'title': rec.title,
            'category': rec.category,
            'priority': rec.priority,
            'impact': f"+{rec.impact * 10:.1f} points",
            'effort': rec.effort,
            'severity': rec.severity,
            'description': rec.description,
            'explanation': rec.explanation,
            'how_to_fix': rec.how_to_fix.split('\n'),
            'code_snippet': rec.code_snippet,
            'before': rec.before_example,
            'after': rec.after_example,
            'estimated_time': rec.estimated_time,
            'resources': rec.resources,
            'tags': rec.tags
        }
    
    def export_as_markdown(self) -> str:
        """Export recommendations as Markdown"""
        md = "# AEO Recommendations\\n\\n"
        
        for rec in self.recommendations:
            md += f"## {rec.title}\\n"
            md += f"**Priority:** {rec.priority}/100 | "
            md += f"**Impact:** +{rec.impact*10:.1f} pts | "
            md += f"**Effort:** {rec.effort}\\n\\n"
            md += f"{rec.description}\\n\\n"
            md += f"### How to Fix\\n{rec.how_to_fix}\\n\\n"
            if rec.code_snippet:
                md += f"### Code\\n```html\\n{rec.code_snippet}\\n```\\n\\n"
            md += "---\\n\\n"
        
        return md
```

---

## 5. COMPLETE RECOMMENDATION ENGINE

```python
class RecommendationEngine:
    def __init__(self, page_data: ExtractedPageData, score_breakdown: Dict):
        self.page_data = page_data
        self.score_breakdown = score_breakdown
        
        self.gap_analyzer = GapAnalyzer(page_data, score_breakdown)
        self.rec_generator = None
        self.formatter = None
    
    def generate_recommendations(self) -> Dict:
        """Complete recommendation generation pipeline"""
        
        # Step 1: Analyze gaps
        gaps = self.gap_analyzer.analyze_all_gaps()
        
        # Step 2: Generate recommendations
        self.rec_generator = RecommendationGenerator(gaps, self.page_data)
        recommendations = self.rec_generator.generate_all()
        
        # Step 3: Format output
        self.formatter = RecommendationFormatter(recommendations)
        formatted = self.formatter.format_for_ui()
        
        return formatted
```

---

## 6. EXAMPLE OUTPUT

```json
{
  "total_recommendations": 12,
  "by_severity": {
    "critical": ["rec_structured_data_jsonld_presence"],
    "high": ["rec_answerability_direct_answer_presence", "rec_structured_data_faq_schema_quality"],
    "medium": ["rec_authority_author_information", "rec_answerability_answer_conciseness"],
    "low": []
  },
  "quick_wins": [
    {
      "id": "rec_answerability_answer_conciseness",
      "title": "Add TL;DR Summary Block",
      "priority": 85,
      "impact": "+6.0 points",
      "effort": "Easy",
      "estimated_time": "15 minutes"
    }
  ],
  "high_impact": [
    {
      "id": "rec_structured_data_jsonld_presence",
      "title": "Add Basic JSON-LD Structured Data",
      "priority": 95,
      "impact": "+8.0 points",
      "effort": "Medium"
    }
  ],
  "all_recommendations": [...]
}
```

---

## NEXT STEPS
- API endpoints to trigger recommendation generation
- Frontend UI to display recommendations
- Change tracking to measure impact of implementations

