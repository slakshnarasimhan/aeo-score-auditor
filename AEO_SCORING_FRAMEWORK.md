# AEO Score Auditor - Scoring Framework

## Overview
The AEO Score is a composite metric (0-100) that evaluates how well a webpage is optimized for Answer Engine Optimization. The score uses 7 weighted buckets with deterministic, explainable sub-scores.

---

## 1. ANSWERABILITY (30 points)

**Purpose**: Measures how well the page directly answers user queries in a consumable format.

### Sub-Scores (30 points total)

#### 1.1 Direct Answer Presence (12 points)
Detects if the page contains direct, concise answers to likely questions.

**Detection Method**:
- Extract all `<p>`, `<div>`, `<span>` blocks
- Identify "answer patterns":
  - Text following question marks
  - Sentences with explicit answer phrases ("The answer is", "This means", "In short")
  - Text in highlighted boxes/callouts
  - Definition patterns ("X is defined as", "X refers to")

**Scoring Formula**:
```
answer_blocks_found = count_answer_patterns()
answer_score = min(12, answer_blocks_found * 2)
```

**Thresholds**:
- 0-1 blocks: 0-2 points (Poor)
- 2-3 blocks: 4-6 points (Fair)
- 4-5 blocks: 8-10 points (Good)
- 6+ blocks: 12 points (Excellent)

---

#### 1.2 Question Coverage (8 points)
Measures how many common user questions the page addresses.

**Detection Method**:
- Extract all text containing `?`
- Identify H2/H3 tags formatted as questions
- Detect "How to", "What is", "Why", "When", "Where" patterns
- Generate expected questions using NLP topic modeling

**Scoring Formula**:
```
questions_answered = count_question_headings() + count_inline_questions()
topic_questions = generate_expected_questions(page_topic)
coverage_ratio = questions_answered / max(topic_questions, 10)
question_score = min(8, coverage_ratio * 8)
```

**Thresholds**:
- 0-2 questions: 0-2 points
- 3-5 questions: 3-5 points
- 6-8 questions: 6-7 points
- 9+ questions: 8 points

---

#### 1.3 Answer Conciseness (6 points)
Evaluates if answers are presented in a scannable, AI-friendly format.

**Detection Method**:
- Check for TL;DR sections
- Detect summary boxes
- Identify bullet point lists
- Find tables with key-value pairs
- Measure average paragraph length

**Scoring Formula**:
```
has_tldr = 2 if detect_tldr_section() else 0
has_bullets = 2 if count_bullet_lists() >= 3 else 0
avg_para_length = calculate_avg_paragraph_words()
concise_paras = 2 if avg_para_length <= 100 else 0
conciseness_score = has_tldr + has_bullets + concise_paras
```

**Thresholds**:
- No structure: 0 points
- Some lists/bullets: 2-3 points
- TL;DR + bullets: 4-5 points
- Fully optimized: 6 points

---

#### 1.4 Answer Block Formatting (4 points)
Checks if answers use visual formatting to highlight key information.

**Detection Method**:
- Detect `<strong>`, `<em>`, `<mark>` tags
- Find callout boxes (`class*="callout|highlight|note"`)
- Identify blockquotes with answers
- Check for answer-specific CSS classes

**Scoring Formula**:
```
has_emphasis = 1 if count_strong_tags() >= 5 else 0
has_callouts = 2 if detect_callout_boxes() else 0
has_blockquotes = 1 if detect_answer_blockquotes() else 0
formatting_score = has_emphasis + has_callouts + has_blockquotes
```

---

## 2. STRUCTURED DATA (20 points)

**Purpose**: Evaluates presence and quality of machine-readable structured data.

### Sub-Scores (20 points total)

#### 2.1 JSON-LD Presence (8 points)
Detects valid JSON-LD blocks.

**Detection Method**:
- Extract all `<script type="application/ld+json">` tags
- Parse JSON and validate against schema.org specs
- Check for syntax errors

**Scoring Formula**:
```
jsonld_blocks = extract_jsonld_blocks()
valid_blocks = [b for b in jsonld_blocks if validate_json(b)]
presence_score = min(8, len(valid_blocks) * 2)
```

**Thresholds**:
- 0 blocks: 0 points
- 1 valid block: 2-3 points
- 2-3 valid blocks: 4-6 points
- 4+ valid blocks: 8 points

---

#### 2.2 Schema Type Relevance (6 points)
Checks if the right schema types are used.

**Detection Method**:
- Extract `@type` from JSON-LD
- Match against expected types for page category:
  - Article, BlogPosting, NewsArticle
  - FAQPage, HowTo, QAPage
  - Product, Review
  - Organization, Person
  - WebPage, AboutPage

**Scoring Formula**:
```
detected_types = extract_schema_types()
expected_types = determine_expected_types(page_content)
relevance_ratio = len(detected_types ∩ expected_types) / len(expected_types)
relevance_score = min(6, relevance_ratio * 6)
```

---

#### 2.3 FAQ Schema Quality (4 points)
Evaluates FAQPage structured data.

**Detection Method**:
- Extract FAQPage schema
- Count question/answer pairs
- Validate each pair has both question and acceptedAnswer

**Scoring Formula**:
```
faq_schema = extract_faq_schema()
if not faq_schema:
    faq_score = 0
else:
    qa_pairs = count_valid_qa_pairs(faq_schema)
    faq_score = min(4, qa_pairs * 0.5)
```

**Thresholds**:
- No FAQ schema: 0 points
- 1-3 Q&A pairs: 1-2 points
- 4-6 Q&A pairs: 2-3 points
- 7+ Q&A pairs: 4 points

---

#### 2.4 Completeness of Required Fields (2 points)
Checks if schema objects have all required properties.

**Detection Method**:
- For each schema type, verify required fields:
  - Article: headline, author, datePublished, image
  - Person: name
  - Organization: name, logo
  - FAQPage: mainEntity array

**Scoring Formula**:
```
schemas = extract_all_schemas()
completeness_scores = []
for schema in schemas:
    required_fields = get_required_fields(schema['@type'])
    present_fields = schema.keys()
    completeness = len(required_fields ∩ present_fields) / len(required_fields)
    completeness_scores.append(completeness)
avg_completeness = mean(completeness_scores) if completeness_scores else 0
completeness_score = avg_completeness * 2
```

---

## 3. AUTHORITY & PROVENANCE (15 points)

**Purpose**: Measures signals of authorship, credibility, and transparency.

### Sub-Scores (15 points total)

#### 3.1 Author Information (5 points)
Detects author bylines and structured author data.

**Detection Method**:
- Extract author from JSON-LD (Article.author)
- Search for byline patterns in HTML
- Check for author bio sections
- Verify author schema with name, url, image

**Scoring Formula**:
```
has_author_jsonld = 2 if extract_author_from_jsonld() else 0
has_author_byline = 1 if detect_author_byline() else 0
has_author_bio = 1 if detect_author_bio_section() else 0
has_full_author_schema = 1 if validate_complete_author_schema() else 0
author_score = has_author_jsonld + has_author_byline + has_author_bio + has_full_author_schema
```

---

#### 3.2 Publication Date (3 points)
Checks for clear publish and update dates.

**Detection Method**:
- Extract datePublished and dateModified from JSON-LD
- Search for date patterns in HTML
- Check meta tags: `article:published_time`, `article:modified_time`

**Scoring Formula**:
```
has_published_date_jsonld = 2 if extract_date_published_jsonld() else 0
has_modified_date = 1 if extract_date_modified() else 0
date_score = has_published_date_jsonld + has_modified_date
```

---

#### 3.3 Citations & Sources (4 points)
Measures external references and source attribution.

**Detection Method**:
- Count external links to authoritative domains
- Detect citation patterns: [1], [2], footnotes
- Find bibliography or references sections
- Check for `rel="nofollow"` vs `rel=""` on citations

**Scoring Formula**:
```
external_links = count_external_links()
authoritative_domains = ['edu', 'gov', 'org', known_publishers]
authority_links = count_links_to_domains(authoritative_domains)
citation_markers = count_citation_markers()
has_references_section = 1 if detect_references_section() else 0

citation_score = min(4, (authority_links * 0.5) + (citation_markers * 0.3) + has_references_section)
```

---

#### 3.4 Organization/Publisher Info (3 points)
Checks for clear publisher identity.

**Detection Method**:
- Extract Organization schema from JSON-LD
- Check for publisher property in Article schema
- Verify organization has logo, name, url

**Scoring Formula**:
```
has_org_schema = 2 if extract_organization_schema() else 0
org_completeness = 1 if validate_org_completeness() else 0
org_score = has_org_schema + org_completeness
```

---

## 4. CONTENT QUALITY & UNIQUENESS (10 points)

**Purpose**: Evaluates depth, originality, and information value.

### Sub-Scores (10 points total)

#### 4.1 Content Depth (4 points)
Measures comprehensive coverage of the topic.

**Detection Method**:
- Count total words (body content only)
- Calculate readability score (Flesch-Kincaid)
- Measure topic coverage using keyword density
- Count number of subtopics (H2 headings)

**Scoring Formula**:
```
word_count = count_body_words()
h2_count = count_h2_headings()
depth_score = 0

if word_count >= 2000:
    depth_score += 2
elif word_count >= 1000:
    depth_score += 1

if h2_count >= 8:
    depth_score += 2
elif h2_count >= 5:
    depth_score += 1
```

**Thresholds**:
- < 500 words, < 3 sections: 0 points
- 500-1000 words, 3-5 sections: 1-2 points
- 1000-2000 words, 5-8 sections: 2-3 points
- 2000+ words, 8+ sections: 4 points

---

#### 4.2 Unique Value Proposition (3 points)
Detects original insights, data, or examples.

**Detection Method**:
- Find tables with original data
- Detect code snippets
- Identify charts/visualizations
- Look for case studies or examples
- Check for step-by-step instructions

**Scoring Formula**:
```
has_tables = 1 if count_data_tables() >= 1 else 0
has_code = 1 if detect_code_blocks() else 0
has_images = 1 if count_informational_images() >= 3 else 0
unique_score = has_tables + has_code + has_images
```

---

#### 4.3 Freshness (3 points)
Evaluates content recency.

**Detection Method**:
- Parse dateModified or datePublished
- Calculate days since last update
- Check if date is visible on page

**Scoring Formula**:
```
last_modified = parse_date_modified()
days_old = (today - last_modified).days

if days_old <= 90:
    freshness_score = 3
elif days_old <= 180:
    freshness_score = 2
elif days_old <= 365:
    freshness_score = 1
else:
    freshness_score = 0
```

---

## 5. CITATION-ABILITY & TRUST (10 points)

**Purpose**: Signals that make content more likely to be cited by AI engines.

### Sub-Scores (10 points total)

#### 5.1 Clear Statements of Fact (4 points)
Detects definitive, quotable statements.

**Detection Method**:
- Extract sentences with high confidence markers
- Identify statistical claims
- Find definition sentences
- Detect "X is Y" patterns

**Scoring Formula**:
```
fact_sentences = extract_fact_patterns()
stat_claims = count_statistical_claims()
definitions = count_definitions()
fact_score = min(4, (len(fact_sentences) * 0.2) + (stat_claims * 0.5) + (definitions * 0.3))
```

---

#### 5.2 Data Tables & Lists (3 points)
Structured information that's easy to extract.

**Detection Method**:
- Count `<table>` elements with 3+ rows
- Count `<ul>` and `<ol>` with 4+ items
- Detect comparison tables

**Scoring Formula**:
```
tables = count_tables_with_min_rows(3)
lists = count_lists_with_min_items(4)
data_score = min(3, (tables * 0.5) + (lists * 0.2))
```

---

#### 5.3 HTTPS & Security (2 points)
Basic trust signals.

**Detection Method**:
- Check if URL uses HTTPS
- Verify SSL certificate validity

**Scoring Formula**:
```
security_score = 2 if is_https_with_valid_cert() else 0
```

---

#### 5.4 No Intrusive Elements (1 point)
Absence of anti-trust signals.

**Detection Method**:
- Check for excessive ads
- Detect aggressive popups
- Check for paywalls

**Scoring Formula**:
```
no_intrusive_score = 1 if not detect_intrusive_elements() else 0
```

---

## 6. TECHNICAL & UX SIGNALS (10 points)

**Purpose**: Technical SEO and user experience factors.

### Sub-Scores (10 points total)

#### 6.1 Page Performance (3 points)
Load speed and Core Web Vitals.

**Detection Method**:
- Measure time to first byte (TTFB)
- Calculate Largest Contentful Paint (LCP)
- Measure Cumulative Layout Shift (CLS)

**Scoring Formula**:
```
lcp_seconds = measure_lcp()
performance_score = 0

if lcp_seconds <= 2.5:
    performance_score = 3
elif lcp_seconds <= 4.0:
    performance_score = 2
elif lcp_seconds <= 6.0:
    performance_score = 1
```

---

#### 6.2 Mobile Friendliness (2 points)
Responsive design check.

**Detection Method**:
- Check viewport meta tag
- Test with mobile user agent
- Verify responsive CSS

**Scoring Formula**:
```
has_viewport = 1 if detect_viewport_meta() else 0
is_responsive = 1 if test_responsive_design() else 0
mobile_score = has_viewport + is_responsive
```

---

#### 6.3 Semantic HTML (2 points)
Proper use of HTML5 semantic elements.

**Detection Method**:
- Check for `<article>`, `<section>`, `<header>`, `<footer>`, `<nav>`
- Verify heading hierarchy (h1 → h2 → h3)

**Scoring Formula**:
```
semantic_tags = count_semantic_tags(['article', 'section', 'header', 'footer'])
valid_hierarchy = check_heading_hierarchy()
semantic_score = min(2, (semantic_tags * 0.3) + (1 if valid_hierarchy else 0))
```

---

#### 6.4 Internal Linking (2 points)
Content interconnection.

**Detection Method**:
- Count internal links
- Check for contextual links (not just navigation)

**Scoring Formula**:
```
internal_links = count_internal_content_links()
linking_score = min(2, internal_links * 0.2)
```

---

#### 6.5 Meta Description (1 point)
Presence of quality meta description.

**Detection Method**:
- Extract meta description tag
- Check length (50-160 characters)

**Scoring Formula**:
```
meta_desc = extract_meta_description()
meta_score = 1 if meta_desc and 50 <= len(meta_desc) <= 160 else 0
```

---

## 7. AI-CITATION SCORE (5 points)

**Purpose**: Actual measurement of AI engine usage.

### Sub-Scores (5 points total)

#### 7.1 Direct Citation Rate (3 points)
How often AI engines cite this page.

**Detection Method**:
- Generate 20 prompts based on page topic
- Query 3 AI engines (GPT-4, Gemini, Perplexity)
- Check if URL appears in responses
- Check for verbatim quotes

**Scoring Formula**:
```
total_queries = 20 * 3  # 60 total
citations = count_url_citations()
verbatim_quotes = count_verbatim_quotes()
citation_rate = (citations + verbatim_quotes) / total_queries
citation_score = min(3, citation_rate * 10)
```

---

#### 7.2 Semantic Alignment (2 points)
How closely AI answers match page content.

**Detection Method**:
- Extract AI responses
- Extract page content
- Compute embedding similarity using sentence transformers
- Calculate average similarity score

**Scoring Formula**:
```
similarities = []
for prompt_response in ai_responses:
    page_embedding = get_embedding(page_content)
    response_embedding = get_embedding(prompt_response)
    similarity = cosine_similarity(page_embedding, response_embedding)
    similarities.append(similarity)
avg_similarity = mean(similarities)
alignment_score = avg_similarity * 2
```

---

## FINAL SCORE CALCULATION

```python
def calculate_aeo_score(page_data):
    scores = {
        'answerability': calculate_answerability(page_data),      # max 30
        'structured_data': calculate_structured_data(page_data),  # max 20
        'authority': calculate_authority(page_data),              # max 15
        'content_quality': calculate_content_quality(page_data),  # max 10
        'citationability': calculate_citationability(page_data),  # max 10
        'technical': calculate_technical(page_data),              # max 10
        'ai_citation': calculate_ai_citation(page_data)           # max 5
    }
    
    total_score = sum(scores.values())
    
    return {
        'overall_score': round(total_score, 1),
        'grade': get_grade(total_score),
        'breakdown': scores
    }

def get_grade(score):
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
```

---

## NORMALIZATION RULES

1. **Missing Data Handling**: If a signal cannot be extracted, score that component as 0
2. **Partial Credit**: Use linear interpolation between thresholds
3. **Domain-Specific Adjustments**: Certain page types (e.g., product pages) may weight different buckets
4. **Confidence Scores**: Track confidence level for each sub-score based on data quality

---

## IMPLEMENTATION NOTES

### Storage Requirements
- Store raw scores for each component
- Store evidence snippets (HTML fragments that contributed to scores)
- Store historical scores for trending
- Store individual AI responses for citation evidence

### Performance Optimization
- Cache embeddings for semantic analysis
- Batch AI queries
- Use async processing for independent score calculations
- Pre-compute common patterns (author detection, schema validation)

### Validation
- Test against benchmark sites with known AEO performance
- Calibrate weights using regression against actual AI citation rates
- A/B test recommendation impacts

---

## EXAMPLE SCORE BREAKDOWN

**Sample Page**: "How to Make Sourdough Bread"

```
Overall Score: 78.5 (B+)

Breakdown:
- Answerability: 24/30
  - Direct Answer Presence: 10/12
  - Question Coverage: 6/8
  - Answer Conciseness: 5/6
  - Answer Block Formatting: 3/4

- Structured Data: 14/20
  - JSON-LD Presence: 6/8
  - Schema Type Relevance: 4/6
  - FAQ Schema Quality: 3/4
  - Completeness: 1/2

- Authority & Provenance: 11/15
  - Author Information: 4/5
  - Publication Date: 2/3
  - Citations & Sources: 3/4
  - Organization Info: 2/3

- Content Quality: 8/10
  - Content Depth: 3/4
  - Unique Value: 3/3
  - Freshness: 2/3

- Citation-ability: 7/10
  - Clear Facts: 3/4
  - Data Tables: 2/3
  - Security: 2/2
  - No Intrusive: 0/1

- Technical & UX: 9/10
  - Performance: 3/3
  - Mobile: 2/2
  - Semantic HTML: 2/2
  - Internal Linking: 1/2
  - Meta Description: 1/1

- AI-Citation: 5.5/5
  - Citation Rate: 3/3
  - Semantic Alignment: 2.5/2
```

---

## NEXT STEPS
This scoring framework provides the foundation. Next deliverables:
- Data extraction specifications
- AI-Citation evaluation algorithms
- Recommendation engine logic

