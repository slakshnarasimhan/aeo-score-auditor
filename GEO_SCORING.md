# GEO (Generative Engine Optimization) Scoring Layer

## Overview

The GEO Score Model evaluates **brand-level inclusion readiness** for generative AI systems (ChatGPT, Gemini, Perplexity). It estimates the likelihood that a brand/site will be included in LLM-generated responses based on site structure, consistency, coverage, and trust signals.

**Important**: This system does NOT claim to predict rankings or guarantee citations. It assesses inclusion readiness only.

## GEO Score Composition (0-100)

```
GEO Score = Brand Knowledge Foundation (30)
          + Topic Ownership & Coverage (25)
          + Cross-Page Consistency (20)
          + AI Recall Signals (15)
          + Contextual Trust Signals (10)
```

---

## Component Breakdown

### 1️⃣ Brand Knowledge Foundation (30 points)

**Purpose**: Measures whether an AI can define the brand clearly.

**Signals**:
- ✅ Canonical "What is X?" or "About" page (10 pts)
- ✅ Organization schema markup (8 pts)
- ✅ Consistent brand mentions across pages (7 pts)
- ✅ Knowledge-focused pages (5 pts)

**Example Evidence**:
```
- Found canonical brand page: /about
- Organization schema on 2 page(s)
- Brand mentioned in 7/7 pages (100%)
- 4 knowledge-focused pages
```

**Why It Matters**: LLMs need a clear, consistent definition of your brand to include it confidently in responses.

---

### 2️⃣ Topic Ownership & Coverage (25 points)

**Purpose**: Measures whether the brand covers its expected topic space with depth.

**Signals**:
- ✅ Topic diversity (5-10 distinct topics) (10 pts)
- ✅ Topic depth (hub + spoke patterns) (10 pts)
- ✅ Intent mix (knowledge + experiential) (5 pts)

**Penalties**:
- ❌ Single-page topic mentions (weak signal)
- ❌ Orphan experiential pages without knowledge anchors

**Example Evidence**:
```
- Strong topic coverage: 10 distinct topics
- Excellent topic depth: 3 topics with multiple pages
- Balanced content mix: knowledge + experiential pages
```

**Why It Matters**: LLMs favor brands that demonstrate expertise across related topics, not just one-off mentions.

---

### 3️⃣ Cross-Page Consistency (20 points)

**Purpose**: Measures semantic consistency to avoid confusing the AI.

**Signals**:
- ✅ Brand name consistency (8 pts)
- ✅ Tone/voice consistency (7 pts)
- ✅ No quality outliers (5 pts)

**Example Evidence**:
```
- Excellent brand consistency: 100% of pages mention brand
- Consistent content tone across pages
- No quality outliers - consistent standard
```

**Why It Matters**: Contradictory or inconsistent information reduces AI confidence in including your brand.

**Note**: This does NOT penalize narrative tone in experiential content.

---

### 4️⃣ AI Recall Signals (15 points)

**Purpose**: Estimates likelihood of implicit recall by LLMs (conservative scoring).

**Signals**:
- ✅ Comparative/list content ("Best X", "Y vs Z") (6 pts)
- ✅ Distinct brand naming (not generic) (5 pts)
- ✅ Question-answering content (4 pts)

**Example Evidence**:
```
- 4 pages with comparative/list content
- Distinct brand name: 'Aprisio'
- 3 pages optimized for Q&A
```

**Why It Matters**: LLMs trained on comparative content and Q&A are more likely to recall brands in relevant contexts.

**Note**: This is probabilistic. High scores don't guarantee citations.

---

### 5️⃣ Contextual Trust Signals (10 points)

**Purpose**: Evaluates whether AI would feel safe including the brand.

**Signals**:
- ✅ HTTPS enabled (3 pts)
- ✅ Author/ownership transparency (4 pts)
- ✅ Date transparency (3 pts)

**Example Evidence**:
```
- HTTPS enabled
- Strong authorship: 6/7 pages
- Dates on 6/7 pages
```

**Why It Matters**: LLMs (especially in products like Perplexity) prefer citing trustworthy sources with clear provenance.

---

## Test Results

### Test Case 1: Luxury Experiential Brand (Aprisio-like)
**Score**: 71/100 ✅

**Strengths**:
- Perfect consistency (20/20)
- Strong topic coverage (22/25)
- Excellent trust signals (10/10)

**Weaknesses**:
- Missing canonical "About" page
- Low AI recall signals (7/15)

**Summary**: "Aprisio shows excellent GEO readiness with a focus on experiential content, particularly in topic coverage and consistency."

---

### Test Case 2: SaaS Documentation-Heavy
**Score**: 80/100 ✅ (adjusted from 98 for conservatism)

**Strengths**:
- Perfect brand foundation (30/30)
- Strong topic coverage (23/25)
- Perfect consistency (20/20)
- Perfect trust (10/10)

**Summary**: "TechSaaS shows excellent GEO readiness with strong knowledge-focused content."

---

### Test Case 3: Thin Content Publisher
**Score**: 39/100 ✅

**Weaknesses**:
- Weak brand foundation (2/30)
- Limited topic coverage (12/25)
- No trust signals (3/10)

**Summary**: "Quickblog shows moderate GEO readiness but would benefit from improvements in brand foundation and trust."

---

## Usage

### Input Format

```python
site_data = {
    'siteUrl': 'https://yourbrand.com',
    'pages': [
        {
            'url': 'https://yourbrand.com/page',
            'html': '<html>...</html>',
            'aeoscore': 72,
            'pageIntent': 'EXPERIENTIAL',  # or KNOWLEDGE, TRANSACTIONAL, NAVIGATIONAL
            'pageSummary': 'Brief description of page content',
            'authoritySignals': {
                'hasAuthor': True,
                'hasOrgSchema': True,
                'hasDates': True
            }
        },
        # ... more pages
    ]
}
```

### Python Example

```python
from scoring.geo_scorer import GEOScorer

scorer = GEOScorer()
result = scorer.calculate_geo_score(site_data)

print(f"GEO Score: {result['geo_score']}/100")
print(f"Summary: {result['summary']}")
print("Recommendations:")
for rec in result['recommended_actions']:
    print(f"  - {rec}")
```

### Output Format

```json
{
  "geo_score": 71,
  "components": {
    "brand_foundation": {
      "score": 12,
      "max": 30,
      "evidence": ["Found canonical brand page: /about", ...]
    },
    "topic_coverage": { "score": 22, "max": 25, "evidence": [...] },
    "consistency": { "score": 20, "max": 20, "evidence": [...] },
    "ai_recall": { "score": 7, "max": 15, "evidence": [...] },
    "trust": { "score": 10, "max": 10, "evidence": [...] }
  },
  "summary": "Brand shows excellent GEO readiness...",
  "recommended_actions": [
    "Create a canonical 'About' page",
    "Add Organization schema markup"
  ],
  "brand_name": "YourBrand",
  "pages_analyzed": 5
}
```

---

## Design Constraints

### ✅ What GEO Score IS:
- An estimate of **inclusion readiness**
- Based on **observable signals**
- **Conservative** and grounded
- **Intent-aware** (experiential vs knowledge content)

### ❌ What GEO Score IS NOT:
- A ranking prediction
- A citation guarantee
- Based on model internals
- Making claims about specific LLM behavior

---

## Interpretation Guide

| Score Range | Interpretation | Typical Profile |
|------------|----------------|-----------------|
| 80-100 | Excellent readiness | SaaS with docs, established publishers |
| 60-79 | Strong readiness | Experiential brands, niche authorities |
| 40-59 | Moderate readiness | Early-stage brands, focused sites |
| 20-39 | Limited readiness | Thin content, weak signals |
| 0-19 | Very weak | Minimal content, no structure |

---

## Key Insights

1. **Experiential brands score mid-range (50-75)** - This is expected and appropriate. They excel at consistency and trust but lack Q&A patterns.

2. **Knowledge brands score higher (70-90)** - Documentation, guides, and Q&A content align well with LLM training.

3. **Thin sites score low (<40)** - Lack of depth, structure, and trust signals reduces inclusion likelihood.

4. **Scores are conservative** - Better to under-promise than over-promise.

---

## Integration with AEO Tool

The GEO scorer builds on existing AEO outputs:
- Uses `aeoscore` for quality assessment
- Uses `pageIntent` for content classification
- Uses `authoritySignals` for trust evaluation
- Requires no external data fetching

**Next Steps for Integration**:
1. Add GEO score to domain audit results
2. Display component breakdown in UI
3. Include recommendations in PDF reports
4. Track GEO score changes over time

---

## Future Enhancements

- [ ] Temporal tracking (GEO score trends)
- [ ] Competitive benchmarking
- [ ] Industry-specific profiles
- [ ] External reference validation (when safe)
- [ ] LLM citation tracking (when available via APIs)

---

## References

- AEO Score Model: `/backend/scoring/calculator.py`
- Content Classification: `/backend/crawler/extractors/content_classifier.py`
- Test Cases: `/backend/test_geo_scorer.py`

