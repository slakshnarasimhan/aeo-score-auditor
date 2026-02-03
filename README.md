# AEO/GEO Score Auditor

A production-ready tool to analyze websites and compute an **Answer Engine Optimization (AEO) Score**, with optional **Generative Engine Optimization (GEO)** scoring for domain-wide audits. Get actionable recommendations to improve visibility in AI-powered answer engines (e.g. ChatGPT, Perplexity, Google SGE).

## What is AEO Score?

The AEO Score (0–100) measures how well your content is optimized for AI answer engines across 7 areas:

1. **Answerability** (30 pts) – Clear, direct answers to user questions
2. **Structured Data** (20 pts) – JSON-LD schema implementation
3. **Authority & Provenance** (15 pts) – Author information, citations, credibility
4. **Content Quality** (10 pts) – Depth, uniqueness, freshness
5. **Citation-ability** (10 pts) – Quotable facts, data tables, trust signals
6. **Technical & UX** (10 pts) – Performance, mobile-friendliness, semantics
7. **AI-Citation Score** (5 pts) – Signals for AI engine usage

**Domain audits** also compute a **GEO Score** (0–100) that evaluates brand-level inclusion readiness (brand foundation, topic coverage, consistency, AI recall, trust). See [GEO_SCORING.md](./GEO_SCORING.md) for details.

## Features

- **Single-page audit** – Crawl, extract, and score one URL; returns result immediately.
- **Domain audit** – Discover URLs (sitemap or crawl), audit multiple pages, aggregated score + GEO. Progress via SSE; result when complete.
- **PDF report** – Generate a downloadable PDF from any audit result (page or domain).
- **Content-aware scoring** – Content classification (informational, experiential, etc.) and per-profile scoring.
- **REST API** – All operations available via `/api/v1/audit/*`, `/api/v1/scores`, etc.
- **Web UI** – Next.js frontend: single-page and “Entire Domain” tabs, live progress for domain audits, score breakdown, PDF download.

## Documentation

- [AEO Scoring Framework](./AEO_SCORING_FRAMEWORK.md) – 0–100 scoring breakdown
- [GEO Scoring](./GEO_SCORING.md) – Domain-level GEO model
- [Domain Crawling Guide](./DOMAIN_CRAWLING_GUIDE.md) – How URL discovery and domain audits work
- [Data Extraction Spec](./DATA_EXTRACTION_SPEC.md) – What data is extracted
- [API Data Models](./API_DATA_MODELS.md) – API shapes and usage
- [Recommendation Engine](./RECOMMENDATION_ENGINE.md) – How recommendations are generated

## Tech Stack

**Backend**

- Python 3.11+, FastAPI, Uvicorn
- **Crawling**: Playwright (optional), BeautifulSoup, lxml; configurable fetcher: `hybrid` (default), `playwright`, or `http`
- **Scoring**: Custom AEO calculator + GEO scorer (domain audits)
- **Reporting**: ReportLab (PDF)
- **Optional**: MongoDB, Redis, Celery (present in Docker; core single-page and domain audit run in-process with in-memory progress tracking)

**Frontend**

- Next.js 14, React 18, TypeScript, TailwindCSS
- React Query, Recharts, Framer Motion, Radix UI

**Config**

- `.env` for API keys and options (see below). No `.env.example` in repo; create `.env` as needed.

## Installation

### Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend)
- Docker & Docker Compose (for full stack with MongoDB, Redis, worker)
- Optional: API keys for AI citation features (OpenAI, Google, Perplexity, Anthropic)

### Quick start with Docker

```bash
git clone <repo-url>
cd aeo-score-auditor

# Create .env if you need API keys or overrides (optional)
# Example: OPENAI_API_KEY=sk-... FETCHER_MODE=hybrid

docker-compose up -d
```

- **Frontend**: http://localhost:3000  
- **API**: http://localhost:8000  
- **API docs**: http://localhost:8000/docs  
- **Health**: http://localhost:8000/health  

Frontend uses `NEXT_PUBLIC_API_URL` in Docker (default in compose points at host). For same-machine use, ensure the frontend can reach the backend (e.g. correct host/port).

### Manual setup

**Backend**

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
# Or use requirements.minimal.txt (includes reportlab for PDF)
playwright install chromium   # if using hybrid/playwright fetcher

uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000. Set `NEXT_PUBLIC_API_URL` if the API is not at `http://localhost:8000`.

### Environment variables (optional)

Create a `.env` in the project root (or set in Docker). Backend reads:

- `MONGODB_URL`, `REDIS_URL`, `CELERY_*` – used when MongoDB/Redis/Celery are running
- `OPENAI_API_KEY`, `GOOGLE_API_KEY`, `PERPLEXITY_API_KEY`, `ANTHROPIC_API_KEY` – for AI citation features
- `FETCHER_MODE` – `hybrid` (default), `playwright`, or `http`
- `DEBUG`, `ENVIRONMENT` – app behavior

## Usage

### Web UI

1. Open http://localhost:3000
2. **Single page**: enter URL → “Audit” → result and breakdown
3. **Entire domain**: “Entire Domain” tab → enter domain (e.g. `https://example.com`) → “Audit Entire Domain” → follow progress; when done, view aggregated score, GEO (if applicable), best/worst pages, and download PDF

### API

**Single-page audit (synchronous)**  
Returns full result in the response.

```bash
curl -X POST http://localhost:8000/api/v1/audit/page \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/page"}'
```

Response includes `result` with `overall_score`, `grade`, `breakdown`, `recommendations`, etc.

**Domain audit (asynchronous)**  
Returns a `job_id`; poll progress via SSE or fetch result when complete.

```bash
# Start domain audit
curl -X POST http://localhost:8000/api/v1/audit/domain \
  -H "Content-Type: application/json" \
  -d '{"domain": "https://example.com", "options": {"max_pages": 20}}'
# -> { "job_id": "job_domain_...", "status": "queued", "progress_url": "/api/v1/audit/domain/progress/{job_id}" }

# Stream progress (SSE)
curl -N http://localhost:8000/api/v1/audit/domain/progress/{job_id}

# Get final result (when status is completed/failed)
curl http://localhost:8000/api/v1/audit/domain/result/{job_id}
```

Domain result includes `overall_score`, `grade`, `pages_audited`, `breakdown`, `page_results`, `best_page`, `worst_page`, and when computed `geo_score`.

**PDF report**  
Generate a PDF from any audit result (e.g. from page or domain result).

```bash
curl -X POST http://localhost:8000/api/v1/audit/pdf \
  -H "Content-Type: application/json" \
  -d '{"audit_result": <paste audit result JSON>, "audit_type": "domain", "detailed": false}' \
  --output report.pdf
```

### How domain URL discovery works

1. **Sitemap**: Tries `{domain}/sitemap.xml`, `sitemap_index.xml`, `sitemap-index.xml`. If found, parses URLs (and follows sitemap indexes). Ensure your sitemap only lists URLs for the domain you are auditing.
2. **Crawl**: If no sitemap, crawls from the homepage and follows same-domain links.
3. Pages are capped by `max_pages` (default 100 in the API). See [DOMAIN_CRAWLING_GUIDE.md](./DOMAIN_CRAWLING_GUIDE.md).

## Testing

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

## Example output

- **Page**: Overall score (e.g. 78/100, grade B+), category breakdown, recommendations.
- **Domain**: Aggregated score, pages audited, best/worst page, GEO score and components, PDF export.

## Project structure (high level)

- `backend/` – FastAPI app, audit pipeline, crawler (domain + page), scoring (AEO + GEO), reporting (PDF, recommendations)
- `frontend/` – Next.js app (single page + domain audit UI)
- `docker-compose.yml` – backend, frontend, MongoDB, Redis, Celery worker (optional for core audits)
- Docs: `AEO_SCORING_FRAMEWORK.md`, `GEO_SCORING.md`, `DOMAIN_CRAWLING_GUIDE.md`, `API_DATA_MODELS.md`, etc.

## Roadmap

- **Done**: Single-page and domain audits, AEO + GEO scoring, SSE progress, PDF reports, content-aware scoring, configurable fetcher.
- **Planned**: Richer AI citation integration, persistent job storage, recommendation tracking, historical trends.

## License

MIT – see [LICENSE](./LICENSE).

## Support

- Open a [GitHub issue](https://github.com/yourusername/aeo-score-auditor/issues) for bugs or feature requests.
- See the documentation files in the repo for detailed behavior and API.

---

**Made for better AI discoverability**
