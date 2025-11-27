# AEO Score Auditor

A production-ready tool to analyze websites and compute an **Answer Engine Optimization (AEO) Score**, with actionable recommendations to improve visibility in AI-powered search engines like ChatGPT, Perplexity, and Google SGE.

## 🎯 What is AEO Score?

The AEO Score (0-100) measures how well your content is optimized for AI answer engines across 7 key areas:

1. **Answerability** (30 pts) - Clear, direct answers to user questions
2. **Structured Data** (20 pts) - JSON-LD schema implementation
3. **Authority & Provenance** (15 pts) - Author information, citations, credibility
4. **Content Quality** (10 pts) - Depth, uniqueness, freshness
5. **Citation-ability** (10 pts) - Quotable facts, data tables, trust signals
6. **Technical & UX** (10 pts) - Performance, mobile-friendliness, semantics
7. **AI-Citation Score** (5 pts) - Real measurement of AI engine usage

## 🚀 Features

- **Complete Page Audits**: Crawl, extract, and analyze 50+ data points
- **AI Citation Analysis**: Test with GPT-4, Gemini, and Perplexity to see if they cite your content
- **Actionable Recommendations**: Get specific fixes with code snippets (JSON-LD, HTML, content)
- **Domain Monitoring**: Track scores across multiple pages over time
- **Beautiful Dashboard**: Visualize scores, trends, and recommendations
- **REST API**: Programmatic access to all features

## 📋 Documentation

- [Scoring Framework](./AEO_SCORING_FRAMEWORK.md) - Detailed breakdown of the 0-100 scoring system
- [Data Extraction Spec](./DATA_EXTRACTION_SPEC.md) - What data we extract and how
- [AI Citation Module](./AI_CITATION_MODULE.md) - How we test AI engine citations
- [Recommendation Engine](./RECOMMENDATION_ENGINE.md) - How recommendations are generated
- [API Reference](./API_DATA_MODELS.md) - Complete API documentation
- [Frontend Spec](./FRONTEND_SPEC.md) - UI/UX design specifications
- [MVP Roadmap](./MVP_ROADMAP.md) - 8-week implementation plan

## 🛠️ Tech Stack

**Backend**:
- Python 3.11+
- FastAPI
- Playwright (crawling)
- BeautifulSoup4 (parsing)
- MongoDB (data storage)
- Redis (caching, queues)
- Celery (async tasks)
- Sentence Transformers (semantic analysis)

**Frontend**:
- Next.js 14
- React 18
- TypeScript
- TailwindCSS
- React Query
- Recharts

**AI Engines**:
- OpenAI (GPT-4)
- Google (Gemini)
- Perplexity
- Anthropic (Claude)

## 📦 Installation

### Prerequisites

- Python 3.11+
- Node.js 18+
- MongoDB
- Redis
- API keys for AI services

### Quick Start with Docker

```bash
# Clone repository
git clone <repo-url>
cd aeo

# Copy environment file
cp .env.example .env

# Edit .env and add your API keys
nano .env

# Start all services
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Manual Installation

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Start API server
uvicorn main:app --reload

# Start Celery worker (in another terminal)
celery -A workers.celery_app worker --loglevel=info
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## 🎮 Usage

### Web Interface

1. Navigate to `http://localhost:3000`
2. Enter a URL to audit
3. View the score breakdown and recommendations
4. Implement fixes and re-audit to track improvements

### API

```bash
# Audit a page
curl -X POST http://localhost:8000/api/v1/audit/page \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/page",
    "options": {
      "include_ai_citation": true,
      "wait_for_completion": true
    }
  }'

# Get recommendations
curl http://localhost:8000/api/v1/recommendations?url=https://example.com/page
```

### Python Client

```python
from aeo_client import AEOClient

client = AEOClient('http://localhost:8000', api_key='your_key')

# Audit a page
result = client.audit_page('https://example.com/page', wait=True)
print(f"Score: {result['overall_score']} ({result['grade']})")

# Get recommendations
recs = client.get_recommendations('https://example.com/page')
for rec in recs['quick_wins']:
    print(f"✓ {rec['title']} - Impact: {rec['impact']}")
```

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# E2E tests
npm run test:e2e
```

## 📊 Example Results

```
Overall Score: 78.5 (B+)

Breakdown:
✓ Answerability: 24/30 (80%)
✓ Structured Data: 14/20 (70%)
✓ Authority: 11/15 (73%)
✓ Content Quality: 8/10 (80%)
✓ Citation-ability: 7/10 (70%)
✓ Technical: 9/10 (90%)
✓ AI-Citation: 3.5/5 (70%)

Top Recommendations:
1. Add FAQPage Schema - Impact: +8.0 pts, Time: 20 min
2. Implement Article Schema - Impact: +7.0 pts, Time: 15 min
3. Add TL;DR Summary - Impact: +6.0 pts, Time: 15 min
```

## 🗺️ Roadmap

### MVP (Weeks 1-8) ✅
- Core crawler and data extraction
- Complete scoring engine
- Recommendation generator
- REST API
- Basic frontend dashboard
- AI citation analysis (simplified)

### Phase 2 (Weeks 9-12)
- Advanced AI citation (verbatim quotes, fact attribution)
- Batch domain auditing (100+ pages)
- Scheduled audits
- Email notifications
- PDF/CSV exports

### Phase 3 (Weeks 13-16)
- Multi-user support
- Team collaboration
- Historical trend analysis
- Competitive analysis
- WordPress/CMS plugins

## 💰 Pricing & API Costs

**API Costs (Estimated)**:
- Without AI citation: ~$0.05 per audit
- With AI citation: ~$0.50-1.00 per audit

**Infrastructure** (monthly):
- MongoDB: $25-50
- Redis: $15-30
- Hosting: $100-200
- **Total**: ~$150-300/month

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License - see [LICENSE](./LICENSE) for details

## 📞 Support

- Documentation: [docs.aeoscore.com](https://docs.aeoscore.com)
- Issues: [GitHub Issues](https://github.com/yourusername/aeo/issues)
- Email: support@aeoscore.com

## 🙏 Acknowledgments

Built with inspiration from:
- Schema.org structured data specifications
- Google's Search Quality Guidelines
- OpenAI's best practices for AI-friendly content
- The SEO and AEO community

---

**Made with ❤️ for better AI discoverability**

