# AEO Score Auditor - MVP Roadmap (6-8 Weeks)

## Overview
This roadmap outlines a complete 8-week sprint plan to build a production-ready MVP of the AEO Score Auditor, broken down into weekly sprints with specific deliverables, dependencies, and testing milestones.

---

## PRE-SPRINT: SETUP (Days 1-3)

### Infrastructure Setup

**Tasks**:
- [ ] Set up development environment
- [ ] Initialize Git repository
- [ ] Set up MongoDB Atlas cluster
- [ ] Set up Redis instance
- [ ] Configure AWS S3 bucket
- [ ] Set up CI/CD pipeline (GitHub Actions)

**Deliverables**:
- Project repository structure
- Development, staging, production environments
- Database connections configured

**Team Assignment**:
- DevOps: 1 person, 3 days

---

### API Keys & Services

**Required API Keys**:
- [ ] OpenAI API key (GPT-4)
- [ ] Google Cloud API key (Gemini)
- [ ] Perplexity API key
- [ ] Anthropic API key (Claude)

**Services to Set Up**:
- [ ] MongoDB Atlas
- [ ] Redis Cloud or ElastiCache
- [ ] AWS S3 or equivalent
- [ ] Email service (SendGrid/Mailgun)

**Budget Estimate**:
- OpenAI: $100/month (testing)
- Google: $50/month
- Perplexity: $50/month
- Anthropic: $50/month
- MongoDB: $25/month (M10 cluster)
- Redis: $15/month
- S3: $10/month
- **Total: ~$300/month**

---

## WEEK 1: CORE CRAWLER & DATA EXTRACTION

### Sprint Goals
Build the foundation: page fetcher, content parser, and data extraction pipeline.

### Day 1-2: Page Fetcher

**Tasks**:
- [ ] Implement Playwright-based page fetcher
- [ ] Add retry logic and error handling
- [ ] Implement timeout handling
- [ ] Add performance metrics collection
- [ ] Write unit tests for fetcher

**Files to Create**:
```
/backend
  /crawler
    fetcher.py
    performance.py
    __init__.py
  /tests
    test_fetcher.py
```

**Acceptance Criteria**:
- Can fetch any publicly accessible URL
- Handles JavaScript-rendered content
- Collects performance metrics (LCP, TTFB)
- Returns status codes, redirects, errors gracefully

---

### Day 3-4: Content Parser

**Tasks**:
- [ ] Implement BeautifulSoup-based parser
- [ ] Create structural extractors (headings, paragraphs, lists, tables)
- [ ] Create metadata extractor
- [ ] Create media extractor
- [ ] Write unit tests with sample HTML fixtures

**Files to Create**:
```
/backend
  /crawler
    parser.py
    extractors/
      structural.py
      metadata.py
      media.py
```

**Acceptance Criteria**:
- Extracts all heading hierarchy
- Parses paragraphs, lists, tables
- Extracts meta tags, author, dates
- Handles malformed HTML gracefully

---

### Day 5: Semantic & Schema Extractors

**Tasks**:
- [ ] Implement question detection
- [ ] Implement answer pattern detection
- [ ] Implement JSON-LD extraction
- [ ] Implement schema validation
- [ ] Write comprehensive tests

**Files to Create**:
```
/backend
  /crawler
    extractors/
      semantic.py
      schema.py
```

**Acceptance Criteria**:
- Detects question patterns (How, What, Why, etc.)
- Extracts answer blocks and TL;DR sections
- Parses all JSON-LD blocks
- Validates schema completeness

---

### End of Week 1 Milestone

**Deliverable**: Complete extraction pipeline that can:
- Fetch any URL
- Extract 50+ data points
- Return structured `ExtractedPageData` object
- Handle errors gracefully

**Testing**:
- Unit tests: 80% coverage
- Test against 10 sample websites
- Performance: <30s per page

**Demo**: CLI tool that audits a URL and outputs JSON

```bash
python -m backend.crawler.cli https://example.com/page --output result.json
```

---

## WEEK 2: SCORING ENGINE

### Sprint Goals
Implement the complete scoring framework with all 7 buckets.

### Day 1-2: Core Scoring Infrastructure

**Tasks**:
- [ ] Create scoring base classes
- [ ] Implement feature engineering
- [ ] Create score calculator for each bucket
- [ ] Write tests for score normalization

**Files to Create**:
```
/backend
  /scoring
    base.py
    features.py
    calculator.py
    answerability.py
    structured_data.py
    authority.py
    content_quality.py
    citationability.py
    technical.py
```

**Acceptance Criteria**:
- Each bucket has deterministic scoring
- Sub-scores sum correctly
- Scores normalized to 0-100 range
- Grade assignment (A+ to F)

---

### Day 3-4: Individual Bucket Implementation

**Tasks**:
- [ ] Implement Answerability scoring (30 pts)
- [ ] Implement Structured Data scoring (20 pts)
- [ ] Implement Authority scoring (15 pts)
- [ ] Implement Content Quality scoring (10 pts)
- [ ] Implement Citationability scoring (10 pts)
- [ ] Implement Technical scoring (10 pts)
- [ ] Write comprehensive tests for each

**Acceptance Criteria**:
- All formulas from scoring framework implemented
- Thresholds match specification
- Edge cases handled (missing data, malformed content)

---

### Day 5: Integration & Testing

**Tasks**:
- [ ] Integrate scoring with extraction pipeline
- [ ] Create end-to-end scoring function
- [ ] Test against 20 sample pages
- [ ] Calibrate scoring thresholds
- [ ] Document scoring decisions

**Files to Create**:
```
/backend
  /scoring
    engine.py
  /tests
    test_scoring_integration.py
    fixtures/
      sample_pages/
```

---

### End of Week 2 Milestone

**Deliverable**: Complete scoring engine that produces:
- Overall score (0-100)
- Grade (A+ to F)
- Detailed breakdown for all 7 buckets
- Evidence snippets

**Testing**:
- Unit tests: 85% coverage
- Integration tests with real pages
- Scoring consistency validation

**Demo**: CLI tool that shows scores

```bash
python -m backend.cli audit https://example.com/page
# Output:
# Overall Score: 78.5 (B+)
# Answerability: 24/30
# Structured Data: 14/20
# ...
```

---

## WEEK 3: RECOMMENDATION ENGINE

### Sprint Goals
Build gap analysis and recommendation generation system.

### Day 1-2: Gap Analyzer

**Tasks**:
- [ ] Implement gap detection for all categories
- [ ] Create severity classification
- [ ] Calculate impact and effort scores
- [ ] Write tests for gap detection

**Files to Create**:
```
/backend
  /recommendations
    gap_analyzer.py
    models.py
```

**Acceptance Criteria**:
- Identifies all gaps (current score < max)
- Assigns severity (critical, high, medium, low)
- Calculates impact (potential score gain)
- Estimates effort (0-1 scale)

---

### Day 3-4: Recommendation Generator

**Tasks**:
- [ ] Create recommendation templates (15+ templates)
- [ ] Implement code snippet generators
- [ ] Create priority calculation
- [ ] Generate before/after examples
- [ ] Write tests for each template

**Files to Create**:
```
/backend
  /recommendations
    generator.py
    templates/
      answerability.py
      schema.py
      authority.py
      technical.py
    snippets/
      jsonld.py
      html.py
```

**Acceptance Criteria**:
- Generates specific, actionable recommendations
- Includes working code snippets
- Priority scoring (1-100)
- Estimated implementation time

---

### Day 5: Formatting & Output

**Tasks**:
- [ ] Implement recommendation formatter
- [ ] Create grouping logic (by severity, category, quick wins)
- [ ] Generate markdown export
- [ ] Create recommendation summary stats

**Files to Create**:
```
/backend
  /recommendations
    formatter.py
    exporter.py
```

---

### End of Week 3 Milestone

**Deliverable**: Recommendation engine that produces:
- List of 10-20 prioritized recommendations
- Code snippets for each
- Estimated impact and effort
- Exportable as JSON, Markdown

**Testing**:
- Template coverage: all gap types
- Code snippet validation (syntax check)
- Priority ranking validation

**Demo**: Complete audit with recommendations

```bash
python -m backend.cli audit https://example.com/page --recommendations
# Shows scores + top 10 recommendations with code
```

---

## WEEK 4: API LAYER

### Sprint Goals
Build FastAPI backend with all core endpoints.

### Day 1-2: Core API Setup

**Tasks**:
- [ ] Initialize FastAPI application
- [ ] Set up request/response models (Pydantic)
- [ ] Implement authentication (API keys)
- [ ] Add rate limiting
- [ ] Set up logging and error handling
- [ ] Add CORS configuration

**Files to Create**:
```
/backend
  /api
    main.py
    auth.py
    models.py
    middleware.py
    config.py
```

**Acceptance Criteria**:
- FastAPI app runs on localhost
- API key authentication works
- Rate limiting enforced
- Error responses standardized

---

### Day 3: Audit Endpoints

**Tasks**:
- [ ] POST /api/v1/audit/page
- [ ] POST /api/v1/audit/domain (basic, without full crawling)
- [ ] Implement async job queue (Celery)
- [ ] Create job status tracking
- [ ] Add webhook support

**Files to Create**:
```
/backend
  /api
    routes/
      audit.py
  /workers
    celery_app.py
    tasks.py
```

**Acceptance Criteria**:
- Can submit audit job
- Returns job_id immediately
- Job runs asynchronously
- Status endpoint shows progress

---

### Day 4: Score & Recommendation Endpoints

**Tasks**:
- [ ] GET /api/v1/scores/page
- [ ] GET /api/v1/scores/domain
- [ ] GET /api/v1/recommendations
- [ ] POST /api/v1/recommendations/{id}/implement
- [ ] Add caching with Redis

**Files to Create**:
```
/backend
  /api
    routes/
      scores.py
      recommendations.py
  /cache
    redis_client.py
```

---

### Day 5: Domain & Job Endpoints

**Tasks**:
- [ ] POST /api/v1/domains
- [ ] GET /api/v1/domains/{id}
- [ ] GET /api/v1/jobs/{id}
- [ ] DELETE /api/v1/jobs/{id}
- [ ] Write API tests

**Files to Create**:
```
/backend
  /api
    routes/
      domains.py
      jobs.py
  /tests
    test_api.py
```

---

### End of Week 4 Milestone

**Deliverable**: Complete REST API with:
- All core endpoints functional
- Async job processing
- Authentication & rate limiting
- Comprehensive error handling

**Testing**:
- API tests: 90% coverage
- Load testing: 100 concurrent requests
- Integration tests with database

**Demo**: Postman collection with all endpoints

```bash
# Start API
uvicorn backend.api.main:app --reload

# Test endpoint
curl -X POST http://localhost:8000/api/v1/audit/page \
  -H "Authorization: Bearer test_key" \
  -d '{"url": "https://example.com/page"}'
```

---

## WEEK 5: AI-CITATION MODULE (BASIC)

### Sprint Goals
Implement core AI citation evaluation (simplified version for MVP).

### Day 1-2: Prompt Generation

**Tasks**:
- [ ] Implement prompt generator
- [ ] Create 4 generation strategies
- [ ] Generate 20 prompts per page
- [ ] Write tests

**Files to Create**:
```
/backend
  /ai_citation
    prompt_generator.py
```

**Acceptance Criteria**:
- Generates diverse, relevant prompts
- Uses page questions and keywords
- Creates semantic variations

---

### Day 3-4: LLM Integration

**Tasks**:
- [ ] Implement GPT-4 client
- [ ] Implement Gemini client
- [ ] Implement Perplexity client
- [ ] Add retry logic and rate limiting
- [ ] Create query orchestrator
- [ ] Write integration tests

**Files to Create**:
```
/backend
  /ai_citation
    llm_clients.py
    orchestrator.py
```

**Acceptance Criteria**:
- Can query all 3 engines
- Handles API failures gracefully
- Rate limits respected
- Responses cached in Redis

---

### Day 5: Citation Detection & Scoring

**Tasks**:
- [ ] Implement URL citation detector
- [ ] Implement semantic similarity analyzer
- [ ] Calculate AI citation score (0-5 points)
- [ ] Store evidence

**Files to Create**:
```
/backend
  /ai_citation
    detector.py
    analyzer.py
    scorer.py
```

---

### End of Week 5 Milestone

**Deliverable**: Basic AI citation module that:
- Generates 20 prompts
- Queries 3 AI engines (60 total queries)
- Detects citations
- Computes similarity
- Returns AI citation score (0-5)

**Testing**:
- Test with 5 sample pages
- Validate citation detection accuracy
- Check API cost ($1-2 per audit)

**Demo**: CLI with AI citation analysis

```bash
python -m backend.cli audit https://example.com/page --ai-citation
# Shows: Citation Rate: 15%, Avg Similarity: 0.72, Score: 3.5/5
```

---

## WEEK 6: FRONTEND (PART 1)

### Sprint Goals
Build core React frontend with main dashboard and page detail view.

### Day 1: Project Setup

**Tasks**:
- [ ] Initialize Next.js + TypeScript project
- [ ] Set up TailwindCSS
- [ ] Configure React Query
- [ ] Set up component library structure
- [ ] Create design tokens

**Files to Create**:
```
/frontend
  /src
    /components
    /pages
    /hooks
    /utils
    /styles
  tailwind.config.js
  next.config.js
```

---

### Day 2-3: Core Components

**Tasks**:
- [ ] Create ScoreCircle component
- [ ] Create ScoreBar component
- [ ] Create RecommendationCard component
- [ ] Create Layout components
- [ ] Write Storybook stories

**Files to Create**:
```
/frontend
  /src
    /components
      /score
        ScoreCircle.tsx
        ScoreBar.tsx
      /recommendations
        RecommendationCard.tsx
      /layout
        Header.tsx
        Sidebar.tsx
```

**Acceptance Criteria**:
- Components reusable and typed
- Storybook stories for all
- Responsive design
- Accessibility compliant

---

### Day 4: Main Dashboard Page

**Tasks**:
- [ ] Create dashboard layout
- [ ] Implement quick audit form
- [ ] Show recent audits list
- [ ] Add domain overview cards
- [ ] Connect to API

**Files to Create**:
```
/frontend
  /src
    /pages
      index.tsx
    /components
      /dashboard
        QuickAuditForm.tsx
        RecentAudits.tsx
        DomainCards.tsx
```

---

### Day 5: Page Detail View

**Tasks**:
- [ ] Create page detail layout
- [ ] Show score overview
- [ ] Implement score breakdown (expandable)
- [ ] Show recommendations panel
- [ ] Connect to API

**Files to Create**:
```
/frontend
  /src
    /pages
      page-detail.tsx
    /components
      /page-detail
        ScoreOverview.tsx
        ScoreBreakdown.tsx
        RecommendationsPanel.tsx
```

---

### End of Week 6 Milestone

**Deliverable**: Functional frontend with:
- Main dashboard
- Page detail view with scores
- Recommendations display
- API integration

**Testing**:
- Component tests with Jest/RTL
- E2E tests with Playwright

**Demo**: Working dashboard

```bash
cd frontend && npm run dev
# Open http://localhost:3000
# Submit audit, view results
```

---

## WEEK 7: FRONTEND (PART 2) & INTEGRATION

### Sprint Goals
Complete remaining frontend features and full end-to-end integration.

### Day 1-2: Domain Dashboard

**Tasks**:
- [ ] Create domain dashboard page
- [ ] Show domain overview stats
- [ ] Implement score trend chart
- [ ] Show page leaderboard
- [ ] Add filtering and sorting

**Files to Create**:
```
/frontend
  /src
    /pages
      domain/[domainId].tsx
    /components
      /domain
        DomainOverview.tsx
        ScoreTrend.tsx
        PageLeaderboard.tsx
```

---

### Day 3: Recommendation Detail Modal

**Tasks**:
- [ ] Create recommendation detail modal
- [ ] Show full recommendation details
- [ ] Display code snippets with copy button
- [ ] Show before/after examples
- [ ] Add "Mark as Implemented" action

**Files to Create**:
```
/frontend
  /src
    /components
      /recommendations
        RecommendationModal.tsx
        CodeSnippet.tsx
```

---

### Day 4: Polish & UX

**Tasks**:
- [ ] Add loading states (skeletons)
- [ ] Add empty states
- [ ] Add error states
- [ ] Implement toast notifications
- [ ] Add animations/transitions
- [ ] Mobile responsiveness

**Files to Create**:
```
/frontend
  /src
    /components
      /ui
        Loading.tsx
        EmptyState.tsx
        Toast.tsx
```

---

### Day 5: End-to-End Integration

**Tasks**:
- [ ] Connect all API endpoints
- [ ] Test complete user flows
- [ ] Fix integration bugs
- [ ] Performance optimization
- [ ] Add analytics tracking

---

### End of Week 7 Milestone

**Deliverable**: Complete, integrated application:
- Frontend connected to backend
- All core features working
- Responsive, polished UI
- Error handling throughout

**Testing**:
- E2E test suite covering main flows
- Cross-browser testing
- Mobile testing

**Demo**: Full application walkthrough

---

## WEEK 8: TESTING, DEPLOYMENT & DOCUMENTATION

### Sprint Goals
Production readiness: comprehensive testing, deployment, documentation.

### Day 1: Testing & QA

**Tasks**:
- [ ] Run full test suite
- [ ] Fix all critical bugs
- [ ] Load testing (100 concurrent audits)
- [ ] Security audit
- [ ] Performance optimization

**Testing Checklist**:
- [ ] Unit tests: >85% coverage
- [ ] Integration tests: all endpoints
- [ ] E2E tests: all user flows
- [ ] Load test: 100 concurrent
- [ ] Security: OWASP top 10

---

### Day 2: Deployment Setup

**Tasks**:
- [ ] Set up production database
- [ ] Configure production Redis
- [ ] Set up Docker containers
- [ ] Create docker-compose.yml
- [ ] Configure reverse proxy (Nginx)
- [ ] Set up SSL certificates
- [ ] Configure environment variables

**Files to Create**:
```
/
  Dockerfile.backend
  Dockerfile.frontend
  Dockerfile.worker
  docker-compose.yml
  docker-compose.prod.yml
  nginx.conf
  .env.example
```

---

### Day 3: CI/CD Pipeline

**Tasks**:
- [ ] Create GitHub Actions workflow
- [ ] Set up automated testing
- [ ] Configure deployment to staging
- [ ] Configure deployment to production
- [ ] Add health check endpoints
- [ ] Set up monitoring (Sentry, DataDog)

**Files to Create**:
```
/.github
  /workflows
    test.yml
    deploy-staging.yml
    deploy-production.yml
```

---

### Day 4: Documentation

**Tasks**:
- [ ] Write README.md
- [ ] Create API documentation (OpenAPI/Swagger)
- [ ] Write deployment guide
- [ ] Create user guide
- [ ] Document architecture
- [ ] Add code comments

**Files to Create**:
```
/docs
  README.md
  DEPLOYMENT.md
  USER_GUIDE.md
  ARCHITECTURE.md
  API_REFERENCE.md
  CONTRIBUTING.md
```

---

### Day 5: Launch Prep

**Tasks**:
- [ ] Final testing on production
- [ ] Performance tuning
- [ ] Set up backup strategy
- [ ] Create monitoring dashboards
- [ ] Prepare launch announcement
- [ ] Create demo video

---

### End of Week 8 Milestone

**Deliverable**: Production-ready MVP:
- Deployed to production
- Full documentation
- Monitoring in place
- Ready for users

**Launch Checklist**:
- [x] All tests passing
- [x] Production deployment successful
- [x] SSL configured
- [x] Monitoring active
- [x] Documentation complete
- [x] Backup strategy in place

---

## POST-MVP: FUTURE ENHANCEMENTS (Weeks 9-12)

### Phase 2 Features

**Week 9-10**:
- Advanced AI citation analysis (verbatim quotes, fact attribution)
- Batch domain auditing (crawl 100+ pages)
- Scheduled audits
- Email notifications
- Export reports (PDF, CSV)

**Week 11-12**:
- Multi-user support
- Team collaboration features
- Historical trend analysis
- Competitive analysis (compare to other domains)
- API webhook system
- WordPress/CMS plugins

---

## RESOURCE ALLOCATION

### Team Structure (Recommended)

```
Backend Developer:    2 people
  - Weeks 1-5 (core backend)
  - Weeks 6-8 (API & integration)

Frontend Developer:   2 people
  - Weeks 1-4 (prep, component library)
  - Weeks 5-8 (full frontend)

Full-Stack:          1 person
  - Weeks 4-8 (integration, API)

DevOps:              0.5 person (part-time)
  - Continuous (infrastructure, deployment)

QA Engineer:         1 person
  - Weeks 6-8 (testing)

Total: 5.5 FTE
```

### Alternative: Solo Developer Timeline

If building solo, extend timeline to **12-16 weeks**:
- Weeks 1-4: Backend core
- Weeks 5-6: API layer
- Weeks 7-8: Basic AI citation
- Weeks 9-12: Frontend
- Weeks 13-14: Integration & testing
- Weeks 15-16: Deployment & docs

---

## RISK MITIGATION

### High-Risk Areas

**1. AI API Costs**
- Risk: Costs exceed budget
- Mitigation: 
  - Cache responses aggressively
  - Rate limit AI citation feature
  - Offer as premium add-on

**2. Crawler Reliability**
- Risk: Sites block crawler or have CAPTCHAs
- Mitigation:
  - Rotate user agents
  - Implement CAPTCHA solving service
  - Allow manual HTML upload

**3. Performance at Scale**
- Risk: Slow audits with many pages
- Mitigation:
  - Horizontal scaling with more workers
  - Queue prioritization
  - Batch processing optimizations

---

## SUCCESS METRICS

### MVP Launch Targets

**Week 8 Goals**:
- [ ] 50 pages audited successfully
- [ ] Average audit time: <3 minutes (without AI)
- [ ] Average audit time: <5 minutes (with AI)
- [ ] 95% API uptime
- [ ] <2s page load time (frontend)
- [ ] 10 beta users

**Week 12 Goals**:
- [ ] 500 pages audited
- [ ] 50 active users
- [ ] 90+ average satisfaction score
- [ ] <1% error rate

---

## DEPENDENCIES & PREREQUISITES

### Must Have Before Starting

- [ ] API keys for all LLMs
- [ ] MongoDB Atlas account
- [ ] Redis instance
- [ ] AWS/GCP account for hosting
- [ ] Domain name
- [ ] SSL certificate
- [ ] Payment method for API costs

### Optional But Recommended

- [ ] Sentry account (error tracking)
- [ ] DataDog/New Relic (monitoring)
- [ ] Postman account (API testing)
- [ ] Figma account (design)

---

## BUDGET BREAKDOWN

### Development Costs (8 weeks)

```
Team (5.5 FTE × 8 weeks):
  - @ $100/hr × 40hrs × 8 weeks = $176,000
  OR
  - @ $5000/week per FTE = $220,000

Infrastructure (8 weeks):
  - API costs (testing): $300/month × 2 = $600
  - MongoDB: $25/month × 2 = $50
  - Redis: $15/month × 2 = $30
  - S3: $10/month × 2 = $20
  - Hosting: $50/month × 2 = $100
  - Domain & SSL: $50
  Total: ~$850

Tools & Services:
  - GitHub: $0 (free tier)
  - Sentry: $26/month
  - Postman: $0 (free tier)
  - Total: ~$50

Grand Total (Dev + Infra): $176,850 - $220,850
```

### Ongoing Monthly Costs (Post-Launch)

```
- API costs: $500-1000 (depends on usage)
- MongoDB: $50 (M10 cluster)
- Redis: $30
- S3: $20
- Hosting: $100-200
- Monitoring: $50
- Total: $750-1350/month
```

---

## CONCLUSION

This roadmap provides a clear, actionable path to building the AEO Score Auditor MVP in 8 weeks with a skilled team, or 12-16 weeks solo. The modular approach allows for adjustments based on resources and priorities.

**Key Success Factors**:
1. Start with solid foundation (crawler, extraction)
2. Implement scoring deterministically
3. Keep AI citation simple for MVP
4. Focus on core UX flows
5. Test thoroughly before launch

**Next Steps**:
- Review and approve roadmap
- Assemble team
- Kick off Week 1 sprint

