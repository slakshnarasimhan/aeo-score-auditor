# AEO Scoring Calibration Progress

## Executive Summary

We're implementing systematic calibration to fix significant underscoring issues discovered when testing against Wikipedia (scored 29/100, expected 78-80/100).

### Overall Progress

| Phase | Status | Avg Score | Improvement | Wikipedia Score |
|-------|--------|-----------|-------------|-----------------|
| **Baseline** | ✅ Complete | 27.6/100 | - | 29/100 |
| **Phase 1** | ✅ Complete | 32.0/100 | +4.4 | 47/100 |
| **Phase 2** | ✅ Complete | 36.1/100 | +8.5 | 66/100 |
| **Phase 3** | ✅ Complete | ~38/100 | +10.4 | 68/100 |
| **Target** | 🎯 Goal | 66.5/100 | +38.9 | 78-80/100 |

**Current Progress: 28% gap closed** (from -38.9 to -28.5 points)

---

## Phase 1: Quick Wins (Weight Rebalancing)

**Goal:** Fix obvious underweighting in key categories  
**Status:** ✅ Complete  
**Impact:** +4.4 points average, +18 points on Wikipedia

### Changes Made

#### 1. Authority Scorer (`authority.py`)
- **Max Score:** 15 → 20 (+5)
- **Changes:**
  - Added `_score_domain_trust` (5 points) for domain age and HTTPS
  - Increased author scoring for structured data
  - More generous date recency thresholds
  - Higher citation/external link scores

#### 2. Content Quality Scorer (`content_quality.py`)
- **Max Score:** 10 → 15 (+5)
- **Changes:**
  - Lowered word count thresholds (500 words = 1 pt, 1000+ = 2 pts)
  - More generous heading count thresholds
  - Better scoring for tables/lists/media
  - Extended freshness windows (90 days = 3 pts, 365 days = 1 pt)

#### 3. Technical Scorer (`technical.py`)
- **Max Score:** 10 → 15 (+5)
- **Changes:**
  - Realistic Core Web Vitals thresholds (LCP ≤ 2.5s = 3 pts)
  - Credit for responsive design meta tags
  - Better semantic HTML scoring
  - Internal linking credit based on count
  - Meta description length scoring

#### 4. Structured Data & Citationability
- **Structured Data:** 20 → 25 (+5)
- **Citationability:** 10 → 15 (+5)

**Results:**
- Wikipedia: 29 → 47 (+18 points)
- Average: 27.6 → 32.0 (+4.4 points)

---

## Phase 2: Major Fixes (Answerability & Structured Data Logic)

**Goal:** Fix overly strict pattern matching that penalizes good sites  
**Status:** ✅ Complete  
**Impact:** +4.1 points average, +19 points on Wikipedia

### Changes Made

#### 1. Answerability Scorer (`answerability.py`) - MAJOR OVERHAUL

**Direct Answer Presence (12 points max):**
- OLD: Required explicit answer patterns/blocks
- NEW: Also credits:
  - Strong intro paragraphs (50-200 words) → +4 pts
  - Substantial content (500+ words) → +2 pts
  - Recognizes that quality sites answer questions in prose, not just structured boxes

**Question Coverage (8 points max):**
- OLD: Only counted explicit "?" questions
- NEW: Also credits:
  - H2/H3 headings as implicit questions (10+ headings = 4 pts)
  - Recognizes that encyclopedias/docs use headings instead of literal questions

**Conciseness (6 points max):**
- More generous list thresholds (1 list = 1 pt, 3+ = 2 pts, 5+ = 3 pts)
- Realistic paragraph length (150 words, up from 100)
- Needs multiple paragraphs to judge (≥3)

**Formatting (4 points max):**
- Credits proper heading structure (H1 + 3+ headings = 2 pts)
- Lower emphasis threshold (3 instead of 5)
- Unified answer pattern detection

**Philosophy:** High-quality sites like Wikipedia, MDN, Stack Overflow answer questions through well-structured prose and headings, not necessarily through FAQ schemas or explicit answer boxes.

#### 2. Structured Data Scorer (`structured_data.py`) - COMPLETE REDESIGN

**Old Approach:**
- Heavily penalized sites without JSON-LD
- Required specific schema types
- Inflexible scoring

**New Approach (4 sub-categories):**

1. **Basic Presence (5 pts):** ANY metadata counts
   - JSON-LD: +3 pts
   - Open Graph: +2 pts
   - Microdata: +2 pts

2. **Schema Quality (5 pts):**
   - Core types (Article, WebPage, Organization): +3 pts
   - Rich types (FAQ, HowTo, Breadcrumbs): +2 pts
   - 70%+ complete schemas: +2 pts

3. **Advanced Features (3 pts):**
   - FAQ schema (3+ Q&A pairs): +2 pts
   - Breadcrumbs: +1 pt

4. **Social Metadata (2 pts):**
   - Complete Open Graph: +1 pt
   - Twitter Cards: +1 pt

**Philosophy:** Many excellent sites (Wikipedia, Stack Overflow) don't use Schema.org but have great SEO. They should still score well via alternate signals.

**Results:**
- Wikipedia: 47 → 66 (+19 points)
- Average: 32.0 → 36.1 (+4.1 points)

---

## Phase 3: Fallback Scoring (Sites Without Schema)

**Goal:** Give credit for basic HTML best practices when schema is absent  
**Status:** ✅ Complete  
**Impact:** +1.9 points average, +2 points on Wikipedia

### Changes Made

#### Structured Data Scorer - Fallback Logic

Added fallback scoring for sites without any structured data:
- Good HTML title (>10 chars): +1 pt
- Meta description (>30 chars): +1 pt
- Structured content (5+ headings): +1 pt

**Philosophy:** Sites like Wikipedia don't use JSON-LD but have excellent HTML structure. They deserve credit for basic SEO hygiene.

**Results:**
- Wikipedia: 66 → 68 (+2 points)
- Average: 36.1 → ~38 (+1.9 points)

---

## Remaining Gaps

### 1. Data Extraction Issues (Critical)

Several high-quality sites are scoring extremely low due to failed data extraction:
- **Healthline:** Scoring 9/100 (expected 75) - 0 answerability
- **Medium:** Scoring 10/100 (expected 58) - 0 answerability
- **Blogger:** Scoring 0/100 (expected 42)

**Root Cause:** These are likely JavaScript-heavy sites that require rendering, or have anti-bot protections.

**Impact:** These failures are dragging down the average by ~5-8 points.

**Solution Options:**
1. Implement Playwright/Puppeteer for JS rendering
2. Add retries with different user agents
3. Add site-specific handling for known problematic domains
4. Fall back to graceful scoring when extraction fails completely

### 2. Category-Specific Gaps

Based on Wikipedia Python (68/100, target 80/100):

| Category | Current | Max | Target | Gap |
|----------|---------|-----|--------|-----|
| Answerability | 26 | 30 | 28 | -2 |
| Structured Data | 2 | 15 | 2 | 0 ✅ |
| Authority | 10 | 18 | 14 | -4 |
| Content Quality | 12 | 15 | 10 | +2 ✅ |
| Citationability | 10 | 12 | 10 | 0 ✅ |
| Technical | 8 | 10 | 9 | -1 |
| **Total** | **68** | **100** | **80** | **-12** |

**Opportunities:**
- Authority: -4 points (need better external citation detection)
- Answerability: -2 points (nearly perfect)
- Technical: -1 point (mobile detection might be failing)

---

## Next Steps

### Immediate Priority: Fix Data Extraction

1. **Identify failure patterns:**
   - Test Healthline, Medium, Blogger directly
   - Check crawler logs for errors
   - Identify if it's JS rendering, bot detection, or timeouts

2. **Implement JS rendering:**
   - Add Playwright to crawler
   - Enable for known problematic domains
   - Add configurable timeout/retry logic

3. **Graceful degradation:**
   - When extraction fails, give partial credit for:
     - Domain authority (age, HTTPS, known good domains)
     - Basic HTTP response signals
   - Never score 0 unless the page truly doesn't exist

**Expected Impact:** +5-8 points average

### Secondary: Fine-Tuning

1. **Authority improvements:**
   - Better detection of citations/references
   - Credit for domain reputation (Wikipedia, .edu, .gov)
   - Author bio extraction

2. **Technical improvements:**
   - Better mobile detection (viewport meta tags)
   - More lenient performance thresholds

**Expected Impact:** +2-4 points average

### Target Milestone

After these fixes:
- **Average Score:** 45-50/100 (vs. target 66.5)
- **Wikipedia:** 75-78/100 (vs. target 80)
- **Gap Closed:** 60-70% of the way

---

## Lessons Learned

### 1. Calibration is Multi-Dimensional
It's not just about weights - it's about:
- **Data quality** (extraction must work)
- **Logic flexibility** (recognize different good patterns)
- **Graceful fallbacks** (never fail completely)

### 2. Industry Standards Vary
- Schema.org adoption is lower than expected
- Many excellent sites use proprietary metadata
- HTML best practices matter more than structured data

### 3. Pattern Matching is Hard
- Original scorers were too pattern-specific
- Good content comes in many formats
- Need both strict patterns AND flexible heuristics

### 4. Benchmark-Driven Development Works
- Testing against real sites revealed issues quickly
- Wikipedia was an excellent calibration target
- Need diverse test sites (news, health, tech, etc.)

---

## Technical Debt & Future Work

1. **Add more benchmark sites** (currently 13)
   - Need 50+ sites across all categories
   - Include international sites
   - Test edge cases (forums, e-commerce, etc.)

2. **Automate calibration**
   - ML-based weight optimization
   - A/B testing for scoring changes
   - Regression testing on every commit

3. **Add explainability**
   - Show why each point was awarded/deducted
   - Provide actionable feedback
   - Compare against similar sites

4. **Performance optimization**
   - Current benchmark takes ~5 minutes
   - Need <1 minute for CI/CD
   - Parallel auditing

---

## Summary

**✅ Achievements:**
- Fixed systematic underscoring in 5 major categories
- Redesigned Answerability and Structured Data scorers
- Added fallback logic for sites without schema
- Improved Wikipedia score from 29 → 68 (+135%)

**🚧 Remaining Work:**
- Fix data extraction for JS-heavy sites
- Fine-tune Authority and Technical scorers
- Expand benchmark suite
- Add graceful degradation

**📊 Progress:**
- 28% of the gap closed (38/66.5 points)
- On track to hit 60-70% with extraction fixes
- Need iterative refinement for final 30-40%

**🎯 Confidence Level:** 
- High confidence we can reach 45-50 average (68% of target)
- Medium confidence for 55-60 average (83% of target)
- Need more data/iteration for 65+ average (98% of target)


