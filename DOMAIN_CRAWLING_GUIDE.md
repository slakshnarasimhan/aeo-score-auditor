# Domain Crawling & Expandable Scores Guide

## 🎉 New Features Added!

### 1. ✅ Domain-Wide Auditing
Audit an entire website (multiple pages) and get aggregated scores!

### 2. ✅ Expandable Score Details
Click on any score category to see detailed sub-scores!

---

## 🌐 How to Use Domain Auditing

### Via Frontend (Recommended):

1. **Open**: http://localhost:3000

2. **Click "Entire Domain" tab**

3. **Enter domain**: 
   - `example.com` or
   - `https://example.com` or
   - `blog.hubspot.com`

4. **Click "Audit Entire Domain"**

5. **Wait**: The tool will:
   - Discover URLs (via sitemap.xml or crawling)
   - Audit up to 10 pages (configurable)
   - Show aggregated results

6. **Results Include**:
   - Overall domain score (average across all pages)
   - Pages audited count
   - Score breakdown by category
   - Best performing page 🏆
   - Worst performing page 📉

### Via API:

```bash
curl -X POST http://localhost:8000/api/v1/audit/domain \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "example.com",
    "options": {
      "max_pages": 10
    }
  }'
```

**Response:**
```json
{
  "job_id": "job_domain_abc123",
  "status": "completed",
  "domain": "example.com",
  "result": {
    "domain": "https://example.com",
    "overall_score": 42.5,
    "grade": "F",
    "pages_audited": 10,
    "pages_successful": 9,
    "breakdown": {
      "answerability": {
        "score": 12.5,
        "max": 30,
        "percentage": 41.7
      },
      // ... more categories
    },
    "best_page": {
      "url": "https://example.com/best-article",
      "overall_score": 68.5
    },
    "worst_page": {
      "url": "https://example.com/old-page",
      "overall_score": 18.2
    }
  }
}
```

---

## 🔍 Expandable Score Details

### How It Works:

1. **Audit any page or domain**

2. **See the score breakdown**
   - Each category shows score/max and percentage
   - Color-coded progress bars (red/orange/yellow/green)

3. **Click on any category** (▶ icon)
   - Expands to show detailed sub-scores
   - Example for "Answerability":
     - Direct answer presence: 8
     - Question coverage: 6.5
     - Answer conciseness: 4
     - Answer block formatting: 2

4. **Click again to collapse** (▼ icon)

### Visual Features:

- ✅ **Color Coding**:
  - 🟢 Green: 80-100% (Excellent)
  - 🟡 Yellow: 60-79% (Good)
  - 🟠 Orange: 40-59% (Fair)
  - 🔴 Red: 0-39% (Poor)

- ✅ **Progress Bars**: Visual representation of scores

- ✅ **Smooth Animations**: Expand/collapse with transitions

---

## 🎯 Domain Crawling Strategy

### URL Discovery Methods:

**1. Sitemap.xml (Preferred)**
- Fastest method
- Checks:
  - `https://example.com/sitemap.xml`
  - `https://example.com/sitemap_index.xml`
  - `https://example.com/sitemap-index.xml`
- If found, uses all URLs from sitemap

**2. Web Crawling (Fallback)**
- Starts from homepage
- Follows internal links
- Max depth: 2 levels
- Excludes: login, cart, account pages
- Excludes: PDFs, images, archives

### Limits:

- **Default**: 10 pages per domain
- **Maximum**: 50 pages (to prevent abuse)
- **Concurrent**: 3 pages at a time (to be respectful)

### What Gets Audited:

✅ **Included**:
- Blog posts
- Articles
- Product pages
- Documentation
- Landing pages

❌ **Excluded**:
- Login/logout pages
- Shopping cart
- User account pages
- Media files (PDF, images)
- External links

---

## 📊 Aggregation Logic

### How Scores Are Combined:

1. **Individual Page Audits**:
   - Each page gets its own complete audit
   - Full score breakdown per page

2. **Aggregation**:
   - Overall score = Average of all page scores
   - Each category = Average across all pages
   - Best page = Highest scoring page
   - Worst page = Lowest scoring page

3. **Grade Assignment**:
   - A+ : 90-100
   - A  : 80-89
   - B+ : 70-79
   - B  : 60-69
   - C  : 50-59
   - F  : 0-49

### Example:

If you audit 5 pages with scores: 45, 52, 38, 61, 44

- **Overall Score**: (45+52+38+61+44)/5 = **48.0**
- **Grade**: **F** (below 50)
- **Best Page**: 61/100
- **Worst Page**: 38/100

---

## 🚀 Performance Notes

### Domain Audit Times:

- **3 pages**: ~15-30 seconds
- **10 pages**: ~45-90 seconds
- **50 pages**: ~5-10 minutes

### Tips for Faster Audits:

1. **Start Small**: Test with 3-5 pages first
2. **Use Sitemap**: Faster than crawling
3. **HTTP Fetcher**: Faster than Playwright (use Docker backend)
4. **Filter URLs**: If you have specific pages to audit

---

## 🎨 Frontend Features Summary

### Single Page Audit:
- Enter any URL
- Get instant results
- Expandable score details
- Recommendations

### Domain Audit:
- Enter domain name
- Audits up to 10 pages
- Aggregated scores
- Best/worst page comparison
- Visual analytics

### UI Improvements:
- ✨ Beautiful gradient design
- 📱 Responsive layout
- 🎯 Tab-based navigation
- 📊 Progress bars with colors
- 🔽 Expandable categories
- 🏆 Performance highlights

---

## 📝 Example Use Cases

### Use Case 1: Blog Audit
```
Domain: blog.hubspot.com
Result: Audit 10 recent blog posts
Insight: See which articles score highest for AEO
```

### Use Case 2: Documentation Site
```
Domain: docs.python.org
Result: Audit technical documentation
Insight: Identify pages that need better Q&A format
```

### Use Case 3: E-commerce
```
Domain: shopify.com
Result: Audit product/info pages (not cart/account)
Insight: See how well product pages answer questions
```

### Use Case 4: News Site
```
Domain: bbc.com/news
Result: Audit news articles
Insight: Check if articles are optimized for AI citations
```

---

## 🔧 Configuration

### Adjust Max Pages:

**Via API**:
```json
{
  "domain": "example.com",
  "options": {
    "max_pages": 20
  }
}
```

**Via Frontend**: 
Currently hardcoded to 10 pages. To change:

Edit `frontend/src/app/page.tsx`:
```typescript
body: JSON.stringify({ 
  domain, 
  options: { max_pages: 20 }  // Change this number
}),
```

---

## 🎯 What's Next?

Future enhancements could include:

- [ ] Custom URL filtering (e.g., only /blog/* pages)
- [ ] Scheduled domain audits
- [ ] Historical score tracking
- [ ] Export results to CSV/PDF
- [ ] Compare domains side-by-side
- [ ] Page-by-page drill-down view
- [ ] AI-powered recommendations per page

---

## ✅ Quick Start Checklist

1. [ ] Open http://localhost:3000
2. [ ] Click "Entire Domain" tab
3. [ ] Enter a domain (e.g., `example.com`)
4. [ ] Click "Audit Entire Domain"
5. [ ] Wait for results (30-90 seconds)
6. [ ] Click on any score category to expand details
7. [ ] Review best/worst performing pages
8. [ ] Use insights to improve AEO optimization!

---

**Your tool now has production-ready domain crawling! 🎉**

