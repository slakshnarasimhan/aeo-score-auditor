# Quick Start Guide

Get the AEO Score Auditor running in 10 minutes.

## Prerequisites

Install these on your system:
- Docker & Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for local development)

## Step 1: Get API Keys

You'll need API keys for AI engines. Sign up for:

1. **OpenAI** (GPT-4): https://platform.openai.com/api-keys
2. **Google AI** (Gemini): https://makersuite.google.com/app/apikey
3. **Perplexity**: https://www.perplexity.ai/settings/api
4. **Anthropic** (Claude): https://console.anthropic.com/

## Step 2: Configure Environment

```bash
# Clone repository
git clone <repo-url>
cd aeo

# Copy environment template
cp .env.example .env

# Edit .env file
nano .env
```

Add your API keys to `.env`:
```bash
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AIza...
PERPLEXITY_API_KEY=pplx-...
ANTHROPIC_API_KEY=sk-ant-...
```

## Step 3: Start Services with Docker

```bash
# Start all services (MongoDB, Redis, Backend, Frontend, Worker)
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f backend
```

## Step 4: Access the Application

- **Frontend Dashboard**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Step 5: Run Your First Audit

### Using the Web Interface

1. Open http://localhost:3000
2. Enter a URL (e.g., `https://example.com/blog/post`)
3. Click "Audit Now"
4. Wait 2-3 minutes (or 4-5 minutes with AI citation)
5. View results!

### Using the API

```bash
curl -X POST http://localhost:8000/api/v1/audit/page \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/page",
    "options": {
      "include_ai_citation": true,
      "wait_for_completion": true
    }
  }'
```

### Using Python

```python
import requests

response = requests.post(
    'http://localhost:8000/api/v1/audit/page',
    json={
        'url': 'https://example.com/page',
        'options': {
            'include_ai_citation': True,
            'wait_for_completion': True
        }
    }
)

result = response.json()
print(f"Score: {result['result']['overall_score']}")
```

## Understanding Your Results

### Score Breakdown

Your page receives a score from 0-100 across 7 categories:

1. **Answerability (30pts)**: How well you answer questions
2. **Structured Data (20pts)**: JSON-LD schema quality
3. **Authority (15pts)**: Author info, citations, credibility
4. **Content Quality (10pts)**: Depth and uniqueness
5. **Citation-ability (10pts)**: Quotable facts and data
6. **Technical (10pts)**: Performance and UX
7. **AI-Citation (5pts)**: Real AI usage measurement

### Grade Scale

- **A+ (90-100)**: Excellent AEO optimization
- **A/A- (80-89)**: Strong optimization
- **B/B+ (70-79)**: Good, with room for improvement
- **C (60-69)**: Needs work
- **D/F (<60)**: Significant improvements needed

### Recommendations

Each audit provides 10-20 prioritized recommendations with:
- Impact score (potential points gained)
- Effort estimate (Easy/Medium/Hard)
- Step-by-step instructions
- Code snippets (JSON-LD, HTML)
- Before/after examples

## Troubleshooting

### Services won't start

```bash
# Check Docker is running
docker --version

# View service logs
docker-compose logs backend
docker-compose logs mongodb

# Restart services
docker-compose restart
```

### API errors

```bash
# Check backend logs
docker-compose logs backend

# Verify MongoDB connection
docker exec -it aeo_mongodb mongosh

# Verify Redis connection
docker exec -it aeo_redis redis-cli ping
```

### Slow audits

- First audit downloads browser binaries (one-time)
- AI citation adds 2-3 minutes
- Large pages (10MB+) take longer
- Check network connection

### API key issues

```bash
# Verify keys are set
docker exec aeo_backend printenv | grep API_KEY

# Test OpenAI key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

## Common Tasks

### Stop services

```bash
docker-compose down
```

### View database

```bash
# Connect to MongoDB
docker exec -it aeo_mongodb mongosh

# Inside mongosh:
use aeo_auditor
db.audits.find().pretty()
```

### Clear cache

```bash
# Connect to Redis
docker exec -it aeo_redis redis-cli

# Inside redis-cli:
FLUSHALL
```

### Update code

```bash
# Pull latest changes
git pull

# Rebuild containers
docker-compose down
docker-compose up -d --build
```

## Development Mode

For active development without Docker:

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Start MongoDB and Redis locally or use Docker
docker-compose up -d mongodb redis

# Start API
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Start worker (separate terminal)
celery -A workers.celery_app worker --loglevel=info
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev

# Access at http://localhost:3000
```

## Next Steps

1. **Read Documentation**: See [README.md](./README.md) for full documentation
2. **Explore API**: Visit http://localhost:8000/docs for interactive API docs
3. **Implement Recommendations**: Use code snippets to improve your site
4. **Monitor Progress**: Re-audit after making changes to track improvements
5. **Add Domains**: Set up domain monitoring for multiple sites

## Need Help?

- **Documentation**: See all `.md` files in this repository
- **Issues**: Create a GitHub issue
- **Logs**: Check `docker-compose logs -f`

---

**You're ready to optimize for AI engines! 🚀**

