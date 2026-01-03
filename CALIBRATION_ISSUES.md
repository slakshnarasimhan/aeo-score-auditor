# AEO Score Auditor - Calibration & Benchmarking Issues

## 🚨 Critical Issue Identified

**Problem**: Wikipedia (an AEO gold standard) scored only **29/100** 
**Expected**: Should score **70-85/100** minimum

## Current Scoring Breakdown

### Max Scores per Category
```
Answerability:     30 points
Structured Data:   20 points  
Authority:         15 points
Content Quality:   10 points
Citationability:   10 points
Technical:         10 points
AI Citation:        5 points (optional)
─────────────────────────────
TOTAL:            100 points
```

### What Wikipedia Actually Has (and should score high on)

✅ **Excellent Answerability**
- Direct answers in intro paragraphs
- Extensive Q&A coverage  
- Well-structured content
- **Should score: 25-28/30**

✅ **Good Authority**
- Multiple citations per article (100+ refs)
- Published/modified dates
- Editorial oversight
- **Should score: 12-14/15**

✅ **Excellent Content Quality**
- Comprehensive coverage (5000+ words)
- Proper heading structure
- Fresh/updated regularly
- **Should score: 9-10/10**

✅ **Excellent Citationability**
- High fact density
- Multiple data tables
- Clear, encyclopedic writing
- **Should score: 9-10/10**

✅ **Good Technical**
- Fast loading
- Mobile responsive
- HTTPS enabled
- **Should score: 8-9/10**

❌ **Missing Structured Data**
- Wikipedia deliberately doesn't use JSON-LD schema
- No Article/FAQPage/HowTo markup
- **Scores: 0-2/20**

### Expected Wikipedia Score
```
Answerability:      27/30  (90%)
Structured Data:     2/20  (10%) ← Only weakness
Authority:          13/15  (87%)
Content Quality:    10/10  (100%)
Citationability:    10/10  (100%)
Technical:           9/10  (90%)
─────────────────────────────
EXPECTED TOTAL:     71/100 (B grade)
ACTUAL SCORE:       29/100 (F grade) ❌
```

**Discrepancy: 42 points off!**

---

## Root Causes

### 1. **Over-weighting Structured Data**
**Issue**: Structured data is 20% of total score, but many excellent sites (Wikipedia, Stack Overflow, Reddit) don't heavily use JSON-LD.

**Reality Check**:
- Google ranks Wikipedia #1 for most informational queries
- AI systems cite Wikipedia constantly (Perplexity, ChatGPT)
- Schema markup helps but isn't 20% of AEO value

**Fix Needed**: Reduce structured_data weight from 20 → 10-12 points

---

### 2. **Too Strict Scoring Formulas**
**Issue**: Current formulas may be too harsh. Example from answerability:

```python
# Current (probably too strict)
direct_answer_score = min(12, answer_blocks * 2)
# If no specific "answer blocks" detected = 0 points
# Wikipedia has answers but not in <blockquote> format

# Better approach
if has_intro_paragraph: score += 6
if has_clear_sections: score += 4
if has_definition: score += 2
```

**Fix Needed**: Review all scoring formulas for realistic expectations

---

### 3. **Missing Pattern Recognition**
**Issue**: Tool may not recognize valid patterns that differ from exact expectations.

**Wikipedia's Approach**:
- Answers in first paragraph (not blockquotes)
- References as [1], [2] (not inline citations)
- Dates in "Last edited on" (not in schema)

**Fix Needed**: Add flexible pattern matching

---

### 4. **No Industry Baseline**
**Issue**: No calibration against known good sites.

**Industry Standards** (from Conductor 2026 AEO Report):
- 25% of searches trigger AI Overviews
- 87.4% of AI traffic from ChatGPT
- Healthcare: 48.7% AI appearance rate

**Fix Needed**: Test against benchmark sites and adjust

---

## Industry Standard Tools Comparison

### Semai.ai / Conductor AEO
**What they measure**:
1. AI Overview Appearances (25% of searches)
2. AI Citations (ChatGPT, Perplexity, Gemini)
3. Entity Visibility Rate
4. Brand Search Lift
5. Answer Share (% of AI answers citing you)

**Key Difference**: They focus on **actual AI system behavior**, not just technical factors.

### Our Tool (Current)
**What we measure**:
1. Technical factors (schema, structure)
2. Content quality (word count, headings)
3. Authority signals (citations, dates)

**Missing**: 
- ❌ Actual AI citation tracking
- ❌ AI Overview appearance rate
- ❌ Real-world AEO performance data

---

## Recommended Calibration Process

### Phase 1: Benchmark Testing ⚡ URGENT
Test against known excellent sites:

| Site | Expected Score | Actual Score | Status |
|------|---------------|--------------|--------|
| Wikipedia | 70-85 | **29** ❌ | BROKEN |
| Stack Overflow | 75-85 | ? | Test needed |
| Mayo Clinic | 80-90 | ? | Test needed |
| NYTimes | 70-80 | ? | Test needed |
| MDN Web Docs | 75-85 | ? | Test needed |
| HubSpot Blog | 65-75 | ? | Test needed |

### Phase 2: Score Rebalancing
**Proposed New Weights**:

```
OLD WEIGHTS:
Answerability:     30 pts (30%)
Structured Data:   20 pts (20%) ← TOO HIGH
Authority:         15 pts (15%)
Content Quality:   10 pts (10%) ← TOO LOW
Citationability:   10 pts (10%)
Technical:         10 pts (10%)

NEW WEIGHTS (Suggested):
Answerability:     30 pts (30%) ✓ Keep
Structured Data:   12 pts (12%) ↓ Reduce 
Authority:         18 pts (18%) ↑ Increase
Content Quality:   18 pts (18%) ↑ Increase
Citationability:   12 pts (12%) ↑ Increase
Technical:         10 pts (10%) ✓ Keep
```

**Rationale**:
- Content quality matters more than schema
- Authority crucial for AI trust
- Structured data helpful but not essential

### Phase 3: Formula Adjustment
Review each scorer's formulas:

**Answerability** - Make less strict:
```python
# OLD: Requires specific answer block format
# NEW: Accept multiple answer patterns
- Intro paragraph with definition: +8 pts
- First paragraph < 100 words: +4 pts
- TL;DR or summary section: +3 pts
- FAQ section (any format): +5 pts
```

**Structured Data** - Don't penalize heavily:
```python
# OLD: 0 points if no schema
# NEW: Partial credit for semantic HTML
- Proper HTML5 structure: +4 pts
- Semantic tags (article, section): +2 pts
- Microdata or RDFa: +3 pts
- JSON-LD: +3 pts
```

**Authority** - Recognize more patterns:
```python
# Accept various citation formats:
- [1], [2] notation: Valid ✓
- Inline (Author, Year): Valid ✓
- Footnotes: Valid ✓
- "Sources" section: Valid ✓
```

### Phase 4: Add AI Citation Module (Advanced)
Integrate with real AI systems:

```python
def check_ai_citations(url, domain):
    """Check if content appears in AI systems"""
    score = 0
    
    # Test with Perplexity API
    if appears_in_perplexity(url):
        score += 10
    
    # Test with ChatGPT search (via API)
    if cited_by_chatgpt(domain):
        score += 10
    
    # Check Google AI Overviews (via SERP API)
    if in_google_ai_overview(url):
        score += 10
    
    return min(30, score)  # Max 30 bonus points
```

---

## Quick Fix for Wikipedia Issue

### Immediate Action Items:

1. **Test Wikipedia page right now**:
```bash
curl http://localhost:8000/api/v1/audit/page \
  -H "Content-Type: application/json" \
  -d '{"url": "https://en.wikipedia.org/wiki/Artificial_intelligence"}'
```

2. **Check extraction logs**:
```bash
docker logs aeo_backend | grep -A10 "wikipedia"
```

3. **Review what was extracted**:
- How many headings detected?
- How many questions found?
- Was content properly parsed?
- Were citations counted?

4. **Adjust formulas temporarily**:
```python
# In structured_data.py - reduce penalty
self.max_score = 12  # was 20

# In answerability.py - be more lenient
if word_count > 100 and has_headings:
    score += 8  # Give credit for long, structured content
```

---

## Long-Term Strategy

### Option A: Hybrid Scoring
```
Technical Score (60%):
- Our current scoring system
- Measures implementation quality
- 0-100 scale

AI Performance Score (40%):
- Real AI citation data
- AI Overview appearances
- Brand search lift
- Requires API integrations
```

### Option B: Weighted Percentiles
Compare against database of 10,000+ audited sites:
```
Your Score: 65/100
Percentile: 72nd (better than 72% of sites)
Industry Average: 58/100
Top 10%: 85+/100
```

### Option C: Site-Type Specific Scoring
```
Blog Post: Focus on answerability (40%)
E-commerce: Focus on structured data (30%)
News Article: Focus on authority (35%)
Tutorial: Focus on structured data + content (60%)
```

---

## Testing Plan

### Step 1: Create Benchmark Suite
```python
BENCHMARK_SITES = {
    'gold_standard': [
        'https://en.wikipedia.org/wiki/Machine_learning',
        'https://stackoverflow.com/questions/1',
        'https://www.mayoclinic.org/diseases-conditions/diabetes'
    ],
    'good': [
        'https://www.hubspot.com/marketing',
        'https://www.nytimes.com/section/technology'
    ],
    'average': [
        'https://medium.com/@author/post',
        'https://www.reddit.com/r/programming'
    ],
    'poor': [
        'content-farm-site.com',
        'thin-affiliate-site.com'
    ]
}
```

### Step 2: Run Benchmark Tests
```bash
python benchmark_calibration.py \
  --sites benchmark_sites.json \
  --output calibration_report.json
```

### Step 3: Analyze Results
```
Expected vs Actual scores
Category-wise breakdown
Identify systematic biases
```

### Step 4: Adjust Weights
```python
# Iteratively adjust until:
# - Wikipedia: 70-85
# - Stack Overflow: 75-85
# - Mayo Clinic: 80-90
```

---

## Comparison: This Tool vs Semai.ai

| Feature | Our Tool | Semai.ai / Conductor |
|---------|----------|---------------------|
| **Structured Data Check** | ✅ Deep | ✅ Yes |
| **Content Analysis** | ✅ Yes | ✅ Yes |
| **Authority Signals** | ✅ Yes | ✅ Yes |
| **AI Citation Tracking** | ❌ No | ✅ **Core feature** |
| **AI Overview Monitoring** | ❌ No | ✅ **Core feature** |
| **Brand Search Lift** | ❌ No | ✅ Yes |
| **Entity Visibility** | ❌ No | ✅ Yes |
| **Competitive Analysis** | ❌ No | ✅ Yes |
| **Historical Tracking** | ❌ No | ✅ Yes |
| **Real-time Data** | ❌ No | ✅ Yes |

**Our Advantage**: 
- ✅ Self-hosted (privacy)
- ✅ Detailed recommendations (230+ tips)
- ✅ Free/open-source

**Their Advantage**:
- ✅ Actual AI system data
- ✅ Industry benchmarks
- ✅ Competitive intelligence
- ✅ Calibrated scoring

---

## Action Plan (Priority Order)

### 🔥 **CRITICAL** (Do Now)
1. ✅ Test Wikipedia and document actual extraction
2. ✅ Identify which scorers are broken
3. ✅ Reduce structured_data weight from 20 → 12
4. ✅ Make answerability more lenient

### 🔧 **HIGH** (This Week)
5. ⏳ Create benchmark test suite (10 sites)
6. ⏳ Run calibration tests
7. ⏳ Adjust all scoring formulas
8. ⏳ Add percentile-based grading

### 📊 **MEDIUM** (This Month)
9. ⏳ Integrate with Perplexity API for AI citations
10. ⏳ Add Google AI Overview tracking
11. ⏳ Build competitive comparison feature
12. ⏳ Add historical trend tracking

### 🚀 **LONG-TERM** (Future)
13. ⏳ ChatGPT citation API integration
14. ⏳ Entity visibility tracking
15. ⏳ Brand search lift measurement
16. ⏳ Industry-specific scoring models

---

## Conclusion

**Current State**: Tool is too strict and doesn't match real-world AEO performance. Wikipedia scoring 29/100 proves the calibration is off by ~40 points.

**Root Cause**: 
1. Over-emphasis on structured data (20% weight)
2. Too strict pattern matching
3. No calibration against known good sites
4. Missing actual AI citation data

**Next Steps**:
1. **Immediate**: Test Wikipedia, reduce structured_data weight
2. **Short-term**: Run benchmark suite, adjust formulas
3. **Long-term**: Add AI citation tracking, competitive analysis

**Goal**: Match industry tools like Semai.ai by combining technical analysis with real AI performance metrics.

---

**Status**: 🚨 CALIBRATION NEEDED  
**Priority**: CRITICAL  
**ETA to Fix**: 1-2 weeks for proper calibration

