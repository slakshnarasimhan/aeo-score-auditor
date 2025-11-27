# Handling JavaScript-Rendered Sites

## Current Limitation

The MVP uses HTTP-based fetching (httpx) which:
- ✅ **Fast**: Sub-second response times
- ✅ **Simple**: No browser dependencies
- ✅ **Works for 70%+ of content sites**: Blogs, wikis, static pages
- ❌ **Fails for JS-heavy sites**: SPAs, modern help centers (e.g., Shopify)

## Test Results

| Site Type | Example | Score | Words Extracted | Status |
|-----------|---------|-------|-----------------|--------|
| Simple HTML | example.com | 9.5 | 19 | ✅ Works |
| Static Blog | SEMrush | 35.2 | 2,593 | ✅ Works |
| Wiki | Wikipedia | 38.0 | 36,778 | ✅ Works |
| JS-Rendered | Shopify Help | 9.0 | 6 | ❌ Fails (JS shell only) |

## Solution: Enable Playwright

### Option 1: Local Development (Without Docker)

1. Install Playwright locally:
```bash
cd backend
source venv/bin/activate
pip install playwright
playwright install chromium
```

2. Switch to Playwright fetcher in `orchestrator.py`:
```python
# Change line 14 from:
from .http_fetcher import HTTPFetcher, PageData

# To:
from .fetcher import PlaywrightFetcher as HTTPFetcher, PageData
```

3. Restart the backend:
```bash
uvicorn main:app --reload
```

### Option 2: Docker with Playwright (Advanced)

Uncomment the Playwright installation lines in `backend/Dockerfile`:

```dockerfile
# Uncomment these lines:
RUN playwright install-deps && playwright install chromium
```

Then rebuild:
```bash
docker compose up --build -d
```

**Note**: This requires fixing the package dependency issues documented in DOCKER_NOTES.md

### Option 3: Hybrid Approach (Recommended for MVP)

Use both fetchers and automatically fall back:

```python
# In orchestrator.py
async def extract(self, url: str):
    # Try HTTP first (fast)
    page_data = await self.http_fetcher.fetch(url)
    
    # If content is too small, retry with Playwright
    if len(page_data.html) < 1000:
        logger.info("Small content detected, retrying with Playwright...")
        page_data = await self.playwright_fetcher.fetch(url)
    
    # Continue with parsing...
```

## Why Shopify Help Has Good AEO (When Properly Rendered)

Shopify Help Center **should** score well because it has:
- ✅ Clear question-based navigation
- ✅ Concise answers
- ✅ Well-structured content
- ✅ Good technical performance
- ✅ Comprehensive coverage

**But**: Our tool can't see this content without JavaScript execution.

## Workaround for Testing

Test individual article URLs that might be server-rendered:
- Try documentation sites: ReadTheDocs, GitBook
- Try established blogs: Medium, Dev.to, Hashnode
- Try news sites: TechCrunch, Wired
- Try marketing pages: Most landing pages are server-rendered

## Long-term Solution

For production, implement:
1. **Smart detection**: Check if content is JS-rendered (low word count)
2. **Automatic fallback**: Switch to Playwright for JS sites
3. **Caching**: Cache results to avoid repeated expensive Playwright calls
4. **Queue system**: Use Celery for async Playwright jobs (already in place)
5. **Cost optimization**: Playwright is 5-10x slower, so only use when needed

## API Enhancement

Add a `force_playwright` flag to the audit request:

```json
{
  "url": "https://help.shopify.com/",
  "options": {
    "force_playwright": true,
    "include_ai_citation": true
  }
}
```

This allows users to opt-in for JS-heavy sites.

