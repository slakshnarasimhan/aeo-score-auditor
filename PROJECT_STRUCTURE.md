# AEO Score Auditor - Project Structure

Complete overview of the codebase organization and file purposes.

## Directory Tree

```
aeo/
├── backend/                    # Python FastAPI backend
│   ├── api/                   # API routes and endpoints
│   │   ├── routes/
│   │   │   ├── audit.py      # Audit submission endpoints
│   │   │   ├── scores.py     # Score retrieval endpoints
│   │   │   ├── recommendations.py  # Recommendation endpoints
│   │   │   ├── domains.py    # Domain management
│   │   │   └── jobs.py       # Job status tracking
│   │   ├── auth.py           # Authentication logic
│   │   ├── middleware.py     # Custom middleware
│   │   └── models.py         # Pydantic request/response models
│   │
│   ├── crawler/              # Web crawling and data extraction
│   │   ├── fetcher.py        # Page fetching (Playwright)
│   │   ├── parser.py         # HTML parsing (BeautifulSoup)
│   │   └── extractors/
│   │       ├── structural.py # Headings, paragraphs, lists, tables
│   │       ├── semantic.py   # Questions, answers, topics
│   │       ├── schema.py     # JSON-LD extraction & validation
│   │       ├── metadata.py   # Author, dates, meta tags
│   │       └── media.py      # Images, videos
│   │
│   ├── scoring/              # Scoring engine
│   │   ├── calculator.py     # Main score orchestrator
│   │   ├── features.py       # Feature engineering
│   │   ├── answerability.py  # Answerability bucket (30pts)
│   │   ├── structured_data.py # Structured data bucket (20pts)
│   │   ├── authority.py      # Authority bucket (15pts)
│   │   ├── content_quality.py # Content quality bucket (10pts)
│   │   ├── citationability.py # Citation-ability bucket (10pts)
│   │   └── technical.py      # Technical bucket (10pts)
│   │
│   ├── ai_citation/          # AI citation evaluation
│   │   ├── prompt_generator.py  # Generate test prompts
│   │   ├── llm_clients.py    # LLM API clients (GPT, Gemini, etc.)
│   │   ├── orchestrator.py   # Query orchestration
│   │   ├── detector.py       # Citation detection
│   │   ├── analyzer.py       # Semantic similarity
│   │   └── scorer.py         # AI citation scoring
│   │
│   ├── recommendations/      # Recommendation engine
│   │   ├── gap_analyzer.py   # Gap detection
│   │   ├── generator.py      # Recommendation generation
│   │   ├── formatter.py      # Output formatting
│   │   ├── templates/        # Recommendation templates
│   │   │   ├── answerability.py
│   │   │   ├── schema.py
│   │   │   ├── authority.py
│   │   │   └── technical.py
│   │   └── snippets/         # Code snippet generators
│   │       ├── jsonld.py
│   │       └── html.py
│   │
│   ├── workers/              # Celery async workers
│   │   ├── celery_app.py     # Celery configuration
│   │   └── tasks.py          # Background tasks
│   │
│   ├── database/             # Database operations
│   │   ├── mongodb.py        # MongoDB connection
│   │   └── models.py         # Database models
│   │
│   ├── cache/                # Caching layer
│   │   └── redis_client.py   # Redis operations
│   │
│   ├── tests/                # Test suite
│   │   ├── test_crawler.py
│   │   ├── test_scoring.py
│   │   ├── test_api.py
│   │   └── fixtures/         # Test fixtures
│   │
│   ├── config.py             # Configuration management
│   ├── main.py               # FastAPI app entry point
│   ├── requirements.txt      # Python dependencies
│   └── Dockerfile            # Backend Docker image
│
├── frontend/                 # Next.js frontend
│   ├── src/
│   │   ├── app/             # Next.js 14 app directory
│   │   │   ├── page.tsx     # Main dashboard
│   │   │   ├── audit/
│   │   │   │   └── [id]/page.tsx  # Page detail view
│   │   │   ├── domain/
│   │   │   │   └── [id]/page.tsx  # Domain dashboard
│   │   │   └── layout.tsx   # Root layout
│   │   │
│   │   ├── components/      # React components
│   │   │   ├── dashboard/
│   │   │   │   ├── QuickAuditForm.tsx
│   │   │   │   ├── RecentAudits.tsx
│   │   │   │   └── DomainCards.tsx
│   │   │   ├── score/
│   │   │   │   ├── ScoreCircle.tsx
│   │   │   │   ├── ScoreBar.tsx
│   │   │   │   └── ScoreBreakdown.tsx
│   │   │   ├── recommendations/
│   │   │   │   ├── RecommendationCard.tsx
│   │   │   │   ├── RecommendationModal.tsx
│   │   │   │   └── CodeSnippet.tsx
│   │   │   ├── domain/
│   │   │   │   ├── DomainOverview.tsx
│   │   │   │   ├── ScoreTrend.tsx
│   │   │   │   └── PageLeaderboard.tsx
│   │   │   ├── ui/
│   │   │   │   ├── Button.tsx
│   │   │   │   ├── Card.tsx
│   │   │   │   ├── Modal.tsx
│   │   │   │   └── Loading.tsx
│   │   │   └── layout/
│   │   │       ├── Header.tsx
│   │   │       ├── Sidebar.tsx
│   │   │       └── Footer.tsx
│   │   │
│   │   ├── hooks/           # Custom React hooks
│   │   │   ├── useAudit.ts
│   │   │   ├── useScore.ts
│   │   │   └── useRecommendations.ts
│   │   │
│   │   ├── lib/             # Utilities
│   │   │   ├── api.ts       # API client
│   │   │   ├── utils.ts     # Helper functions
│   │   │   └── constants.ts # Constants
│   │   │
│   │   └── styles/          # Global styles
│   │       └── globals.css
│   │
│   ├── public/              # Static assets
│   ├── package.json         # Node dependencies
│   ├── tsconfig.json        # TypeScript config
│   ├── tailwind.config.js   # Tailwind config
│   └── Dockerfile           # Frontend Docker image
│
├── docs/                     # Documentation
│   ├── AEO_SCORING_FRAMEWORK.md
│   ├── DATA_EXTRACTION_SPEC.md
│   ├── AI_CITATION_MODULE.md
│   ├── RECOMMENDATION_ENGINE.md
│   ├── API_DATA_MODELS.md
│   ├── FRONTEND_SPEC.md
│   └── MVP_ROADMAP.md
│
├── scripts/                  # Utility scripts
│   ├── setup.sh             # Initial setup
│   ├── seed_db.py           # Seed test data
│   └── backup.sh            # Backup script
│
├── .env.example             # Environment template
├── .gitignore               # Git ignore rules
├── docker-compose.yml       # Docker orchestration
├── docker-compose.prod.yml  # Production Docker config
├── README.md                # Project overview
├── QUICKSTART.md            # Quick start guide
├── PROJECT_STRUCTURE.md     # This file
└── LICENSE                  # License file
```

## Key Files Explained

### Backend Core

**`backend/main.py`**
- FastAPI application entry point
- Router registration
- Middleware setup
- Exception handlers

**`backend/config.py`**
- Centralized configuration
- Environment variable management
- Settings validation

**`backend/crawler/fetcher.py`**
- Playwright-based page fetching
- Handles JavaScript rendering
- Performance metrics collection
- Retry logic

**`backend/crawler/parser.py`**
- HTML parsing with BeautifulSoup
- Content extraction
- Noise removal
- Main content identification

**`backend/scoring/calculator.py`**
- Orchestrates all scoring buckets
- Combines sub-scores
- Computes final grade
- Handles scoring errors

### Frontend Core

**`frontend/src/app/page.tsx`**
- Main dashboard page
- Quick audit form
- Recent audits display
- Domain overview

**`frontend/src/components/score/ScoreCircle.tsx`**
- Large circular score display
- Grade badge
- Score change indicator
- Animated reveal

**`frontend/src/components/recommendations/RecommendationCard.tsx`**
- Recommendation display card
- Priority indicator
- Impact and effort display
- Quick actions

**`frontend/src/lib/api.ts`**
- Centralized API client
- Request/response handling
- Error handling
- Authentication

### Configuration Files

**`.env.example`**
- Template for environment variables
- API keys
- Database URLs
- Feature flags

**`docker-compose.yml`**
- Local development orchestration
- Service definitions
- Network configuration
- Volume mounts

**`requirements.txt`**
- Python dependencies
- Version pinning
- Core libraries

**`package.json`**
- Node.js dependencies
- Scripts
- Build configuration

## Code Organization Principles

### Backend

1. **Separation of Concerns**: Each module has a single responsibility
2. **Dependency Injection**: Services are injected, not imported
3. **Error Handling**: Graceful degradation at all levels
4. **Type Safety**: Pydantic models for validation
5. **Async First**: All I/O operations are async

### Frontend

1. **Component-Based**: Reusable, composable components
2. **Type Safety**: Full TypeScript coverage
3. **Server Components**: Use React Server Components where possible
4. **Client State**: Minimal client state, prefer server state
5. **Accessibility**: WCAG 2.1 AA compliance

## Development Workflow

### Adding a New Scoring Metric

1. Update scoring framework docs (`AEO_SCORING_FRAMEWORK.md`)
2. Create scorer class in `backend/scoring/`
3. Add to `calculator.py`
4. Add extraction logic in `backend/crawler/extractors/`
5. Update tests
6. Update frontend display components

### Adding a New API Endpoint

1. Define Pydantic models in `backend/api/models.py`
2. Create route in `backend/api/routes/`
3. Add to router in `main.py`
4. Update API docs (`API_DATA_MODELS.md`)
5. Update frontend API client
6. Add tests

### Adding a New Recommendation Template

1. Create template function in `backend/recommendations/templates/`
2. Add to generator mapping in `generator.py`
3. Add code snippet generator if needed
4. Update tests
5. Update frontend modal display

## Testing Structure

```
backend/tests/
├── unit/              # Unit tests
│   ├── test_fetcher.py
│   ├── test_parser.py
│   └── test_scoring.py
├── integration/       # Integration tests
│   ├── test_api.py
│   └── test_pipeline.py
└── fixtures/          # Test data
    ├── sample_pages/
    └── mock_responses/

frontend/tests/
├── components/        # Component tests
├── integration/       # Integration tests
└── e2e/              # End-to-end tests
```

## Build & Deployment

### Development
```bash
# Backend
cd backend && uvicorn main:app --reload

# Frontend
cd frontend && npm run dev
```

### Production
```bash
# Build Docker images
docker-compose -f docker-compose.prod.yml build

# Deploy
docker-compose -f docker-compose.prod.yml up -d
```

## Environment Variables by Service

### Backend
- `MONGODB_URL`
- `REDIS_URL`
- `OPENAI_API_KEY`
- `GOOGLE_API_KEY`
- `PERPLEXITY_API_KEY`
- `ANTHROPIC_API_KEY`

### Worker
- Same as backend

### Frontend
- `NEXT_PUBLIC_API_URL`

## Monitoring & Logs

- Backend logs: `docker-compose logs -f backend`
- Worker logs: `docker-compose logs -f worker`
- Database: `docker exec -it aeo_mongodb mongosh`
- Cache: `docker exec -it aeo_redis redis-cli`

---

**This structure is designed for scalability, maintainability, and developer experience.**

