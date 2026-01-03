# Quick Start: JavaScript Rendering for AEO Auditor

## Summary

Your AEO auditor now supports JavaScript-heavy websites! 🎉

## What Changed

✅ **Hybrid Fetcher** - Automatically detects when JavaScript rendering is needed  
✅ **Playwright Integration** - Full browser automation with Chromium  
✅ **Smart Detection** - Uses fast HTTP for static sites, Playwright for JS-heavy sites  
✅ **Zero Configuration** - Works out of the box

## How to Use

### 1. Rebuild Docker Containers (One Time)

```bash
cd /home/narasimhan/workarea/aeo
docker compose down
docker compose build backend worker
docker compose up -d
```

⏱️ **Build time:** ~2-3 minutes (downloads Chromium browser)

### 2. Verify It's Working

```bash
# Check logs for fetcher mode
docker compose logs backend | grep -i "fetcher"

# Should see:
# "Using Hybrid fetcher (auto-detects when JavaScript is needed)"
```

### 3. Test a JS-Heavy Site

```bash
# Test Healthline (known JS-heavy site)
curl -X POST http://localhost:8000/api/v1/audit/page \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.healthline.com/nutrition/foods-high-in-vitamin-d"}'
```

### 4. Use the Web Interface

Open http://localhost:3000 and audit any URL - it will automatically use the right fetcher!

## How It Works

```
User submits URL
    ↓
Is domain in JS_HEAVY_SITES list?
    ├─ YES → Use Playwright (2-4s, full JS support)
    └─ NO  → Try HTTP first (200ms, fast)
        ↓
    Assess content quality
        ├─ GOOD → Return HTTP result ✅
        └─ POOR → Retry with Playwright 🔄
```

## Supported Sites

### Works Perfectly
- Wikipedia, MDN, Stack Overflow
- Most documentation sites
- Static HTML sites
- Basic JavaScript sites

### Works with Limitations
- Healthline, WebMD (anti-bot protection)
- Medium (paywalls)
- Blogger (varies)

### How to Add More JS-Heavy Sites

Edit `backend/crawler/hybrid_fetcher.py`:

```python
JS_HEAVY_SITES = {
    'healthline.com',
    'medium.com',
    'your-site-here.com',  # Add here!
}
```

Then restart:

```bash
docker compose restart backend worker
```

## Configuration Options

Set in `docker-compose.yml`:

```yaml
environment:
  # Choose fetcher mode:
  - FETCHER_MODE=hybrid    # Default: Auto-detect (recommended)
  # - FETCHER_MODE=playwright  # Always use JS rendering (slow but reliable)
  # - FETCHER_MODE=http        # Never use JS rendering (fast but limited)
```

## Performance

| Mode | Speed | Compatibility | Use When |
|------|-------|---------------|----------|
| **hybrid** | Medium | High | General use (default) |
| playwright | Slow | Highest | All targets need JS |
| http | Fast | Medium | All targets are static |

## Troubleshooting

### "Playwright not found"
```bash
docker compose build --no-cache backend worker
docker compose up -d
```

### "Sites still scoring low"
Some sites have aggressive bot detection. This is normal. See `JAVASCRIPT_RENDERING.md` for advanced evasion techniques.

### "Too slow"
```yaml
# In docker-compose.yml, switch to HTTP mode for static sites:
environment:
  - FETCHER_MODE=http
```

## Files Changed

- ✅ `backend/crawler/hybrid_fetcher.py` - New hybrid fetcher
- ✅ `backend/crawler/orchestrator.py` - Updated to use hybrid fetcher
- ✅ `backend/Dockerfile` - Added Playwright dependencies
- ✅ `docker-compose.yml` - Added FETCHER_MODE configuration
- ✅ `JAVASCRIPT_RENDERING.md` - Full documentation
- ✅ `JS_RENDERING_TEST_RESULTS.md` - Test results and analysis

## What's Next?

For even better results with problematic sites:

1. **Add stealth mode** - Evade bot detection
2. **Implement caching** - Speed up repeated audits
3. **Add proxy rotation** - Avoid IP bans
4. **Site-specific handlers** - Custom logic for tricky sites

See `JAVASCRIPT_RENDERING.md` for details!

## Quick Test Commands

```bash
# Test Wikipedia (should use HTTP - fast)
curl -X POST http://localhost:8000/api/v1/audit/page \
  -H "Content-Type: application/json" \
  -d '{"url": "https://en.wikipedia.org/wiki/Python_(programming_language)"}' \
  | jq '.result.overall_score'

# Test Healthline (should use Playwright - slower)
curl -X POST http://localhost:8000/api/v1/audit/page \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.healthline.com/nutrition/foods-high-in-vitamin-d"}' \
  | jq '.result.overall_score'

# Check which fetcher was used
docker compose logs backend | tail -30 | grep -i "fetcher"
```

## Success! 🎉

Your AEO auditor now intelligently handles both static and JavaScript-heavy websites!


