# How to Enable Playwright for JavaScript-Heavy Sites

## Current Status: HTTP Fetcher (Fast & Simple)

By default, the tool uses **HTTP fetching** which:
- ✅ Works for 70%+ of sites (blogs, wikis, static pages)
- ✅ Fast (sub-second response times)
- ✅ No heavy dependencies
- ❌ Fails for JS-rendered sites (SPAs, React/Vue apps)

## Option 1: Enable Playwright Locally (Recommended)

**Best for development and testing JS-heavy sites.**

### Step 1: Install Playwright in Your Local Environment

```bash
cd backend
source venv/bin/activate  # or activate your venv
pip install playwright
playwright install chromium
```

### Step 2: Run Backend Locally (Not in Docker)

```bash
# In backend/ directory
export USE_PLAYWRIGHT=true
uvicorn main:app --reload --port 8000
```

### Step 3: Keep Other Services in Docker

```bash
# In project root
docker compose up mongodb redis -d
```

Now your local backend will use Playwright and can handle JS sites like Shopify Help!

## Option 2: Enable in Docker (Advanced)

**Requires fixing Playwright browser installation in Docker.**

### Step 1: Update Dockerfile

Uncomment the Playwright installation in `backend/Dockerfile`:

```dockerfile
# Playwright installation (optional, uncomment for JS-heavy sites)
RUN playwright install-deps chromium && playwright install chromium
```

### Step 2: Update docker-compose.yml

```yaml
services:
  backend:
    environment:
      - USE_PLAYWRIGHT=true  # Changed from false
```

### Step 3: Rebuild

```bash
docker compose down
docker compose up --build -d
```

**Note**: This may fail due to package dependency conflicts in Docker. If it fails, use Option 1 instead.

## Option 3: Hybrid Mode (Smart Fallback)

**Automatically detect JS-heavy sites and use appropriate fetcher.**

Add to `backend/crawler/orchestrator.py` in the `extract()` method:

```python
async def extract(self, url: str) -> ExtractedPageData:
    # Try HTTP first (fast)
    page_data = await self.http_fetcher.fetch(url)
    
    # If content is suspiciously small, retry with Playwright
    if len(page_data.html) < 1000 and not page_data.error:
        logger.warning(f"Small HTML detected ({len(page_data.html)} bytes), retrying with Playwright...")
        try:
            playwright_fetcher = PlaywrightFetcher()
            page_data = await playwright_fetcher.fetch(url)
        except Exception as e:
            logger.error(f"Playwright fallback failed: {e}")
    
    # Continue with parsing...
```

## Testing Playwright is Working

Once enabled, test with a JS-heavy site:

```bash
curl -X POST http://localhost:8000/api/v1/audit/page \
  -H "Content-Type: application/json" \
  -d '{"url": "https://help.shopify.com/"}'
```

**Expected Results:**

| Fetcher | Word Count | Score | Status |
|---------|------------|-------|--------|
| HTTP (current) | ~6 words | 9/100 | ❌ Only sees JS shell |
| Playwright | ~2000+ words | 40-60/100 | ✅ Sees real content |

## Troubleshooting

### "Playwright not available" Warning

```bash
# Solution: Install Playwright
pip install playwright
playwright install chromium
```

### Segmentation Fault in Docker

This is a known issue with Playwright in Docker. Use **Option 1 (Local)** instead.

### Network/DNS Errors

```bash
# If using Microsoft's Playwright image
# Solution: Use local installation or different base image
```

### Still Getting Low Scores

Even with Playwright, some sites may score low because they lack:
- Schema.org structured data (-20 points)
- Author/date information (-15 points)
- Q&A format (-10-20 points)

This is **correct behavior** - the site genuinely lacks AEO optimization!

## Performance Comparison

| Method | Speed | JS Support | Setup Difficulty |
|--------|-------|------------|------------------|
| HTTP Fetcher | ⚡ <1s | ❌ No | ✅ Easy (default) |
| Playwright | 🐢 3-5s | ✅ Yes | ⚠️ Medium |
| Hybrid | ⚡ 1s (HTTP) or 🐢 4s (PW) | ✅ Auto | ⚠️ Advanced |

## Recommendation

For most users:
1. **Use HTTP fetcher (current default)** for fast audits of traditional sites
2. **Enable Playwright locally (Option 1)** when you need to audit specific JS-heavy sites
3. **Don't bother with Docker Playwright** unless you have specific deployment requirements

The tool is already production-ready with HTTP fetching!

