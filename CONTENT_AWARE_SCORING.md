# Content-Aware Scoring

## Overview

The AEO Score Auditor now uses **content-aware scoring** to evaluate pages based on their purpose and intent. Different types of content have different priorities, and the scoring system adapts accordingly.

## Content Types

### 1. **Informational** (Articles, Guides, Tutorials, FAQs)
- **Focus**: Answering questions, providing information, education
- **Higher weights**: Answerability (1.3x), Authority (1.2x), Content Quality (1.2x), Citationability (1.2x)
- **Lower weights**: None
- **Best for**: Blog posts, how-to guides, educational content, documentation

### 2. **Experiential** (Experiences, Stories, Events, Travel)
- **Focus**: Storytelling, evoking emotion, sharing experiences
- **Higher weights**: Structured Data (1.3x for Event/Place schema)
- **Lower weights**: Answerability (0.5x), Citationability (0.6x)
- **Best for**: Travel experiences, event pages, personal stories, showcases

### 3. **Transactional** (Products, Services, E-commerce)
- **Focus**: Commerce, clear specifications, trust signals
- **Higher weights**: Structured Data (1.4x for Product schema), Technical (1.2x)
- **Lower weights**: Answerability (0.8x), Content Quality (0.9x), Citationability (0.7x)
- **Best for**: Product pages, service offerings, e-commerce listings

### 4. **Navigational** (Category Pages, Hubs, Indices)
- **Focus**: Organization, easy navigation, performance
- **Higher weights**: Structured Data (1.2x), Technical (1.3x)
- **Lower weights**: Answerability (0.6x), Content Quality (0.7x), Citationability (0.5x)
- **Best for**: Category pages, archive pages, navigation hubs

## How It Works

### Automatic Detection

The system automatically detects content type using multiple signals:

1. **Explicit declaration** (highest priority)
   ```html
   <meta name="aeo:content-type" content="experiential">
   ```

2. **Schema.org types**
   - `Article`, `BlogPosting` → Informational
   - `Event`, `Place`, `TouristAttraction` → Experiential
   - `Product`, `Offer` → Transactional
   - `CollectionPage`, `ItemList` → Navigational

3. **URL patterns**
   - `/experience/`, `/event/`, `/tour/` → Experiential
   - `/blog/`, `/guide/`, `/how-to/` → Informational
   - `/product/`, `/shop/` → Transactional
   - `/category/`, `/archive/` → Navigational

4. **Content heuristics**
   - Keyword analysis (experience, journey, story vs. how to, guide, learn)
   - Structural patterns (image galleries, forms, Q&A sections)

5. **Confidence levels**
   - **High**: Multiple strong signals agree
   - **Medium**: Some signals present
   - **Low**: Weak or conflicting signals (defaults to informational)

## Examples

### Experiential Content Example

**Before Content-Aware Scoring:**
```
"The Art of the Pour" experience page
Score: 35/100 ❌
- Lost points for not having Q&A patterns
- Lost points for not being factual/citation-heavy
```

**After Content-Aware Scoring:**
```
"The Art of the Pour" experience page
Content Type: Experiential (high confidence)
Score: 68/100 ✅
- Answerability weight reduced (0.5x)
- Citationability weight reduced (0.6x)
- Structured Data weight increased (1.3x)
- Valued for storytelling and imagery
```

### Mixed Site Example

For a site like Aprisio with both experiences and blog posts:
- `/experiences/the-art-of-the-pour` → Scored as **Experiential**
- `/blog/how-to-plan-your-trip` → Scored as **Informational**
- Each page optimized for its purpose!

## Manual Override

If automatic detection doesn't match your intent, add this to your HTML `<head>`:

```html
<!-- Force experiential scoring -->
<meta name="aeo:content-type" content="experiential">

<!-- Force informational scoring -->
<meta name="aeo:content-type" content="informational">

<!-- Force transactional scoring -->
<meta name="aeo:content-type" content="transactional">

<!-- Force navigational scoring -->
<meta name="aeo:content-type" content="navigational">
```

## Scoring Adjustments by Type

| Category | Default | Informational | Experiential | Transactional | Navigational |
|----------|---------|---------------|--------------|---------------|--------------|
| Answerability | 1.0x | 1.3x | 0.5x | 0.8x | 0.6x |
| Structured Data | 1.0x | 1.0x | 1.3x | 1.4x | 1.2x |
| Authority | 1.0x | 1.2x | 0.9x | 1.1x | 0.8x |
| Content Quality | 1.0x | 1.2x | 1.1x | 0.9x | 0.7x |
| Citationability | 1.0x | 1.2x | 0.6x | 0.7x | 0.5x |
| Technical | 1.0x | 1.0x | 1.0x | 1.2x | 1.3x |

## Benefits

1. **Fair Evaluation**: Pages are judged by their intent, not a one-size-fits-all standard
2. **Better Scores**: Experiential content no longer penalized for lack of Q&A
3. **Clearer Direction**: Recommendations match your content goals
4. **Flexibility**: Works automatically but can be overridden
5. **Transparency**: Shows content type and confidence in results

## Implementation Status

✅ Content type classification  
✅ Scoring profiles for all 4 types  
✅ Weight application in calculator  
✅ Frontend display of content type  
✅ Automatic multi-signal detection  
✅ Manual override via meta tags  

## Future Enhancements

- [ ] Per-category recommendations based on content type
- [ ] Content type distribution report for domains
- [ ] Custom scoring profiles via configuration
- [ ] Machine learning for better classification

---

**Pro Tip**: For best results on experiential content, add Event or Place schema markup and include rich media (images, videos). The system will recognize this and adjust scoring accordingly!

