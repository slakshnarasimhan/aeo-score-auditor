# AEO Score Auditor - APIs & Data Models

## Overview
Complete REST API specification and database schemas for the AEO Score Auditor platform.

---

## API ARCHITECTURE

```
Client (React)
    ↓
API Gateway (FastAPI)
    ├── /api/v1/audit       → Audit endpoints
    ├── /api/v1/scores      → Score retrieval
    ├── /api/v1/recommendations → Recommendations
    ├── /api/v1/domains     → Domain management
    ├── /api/v1/jobs        → Job status
    └── /api/v1/export      → Data export

Backend Services
    ├── Crawler Service
    ├── Scoring Engine
    ├── AI Citation Service
    ├── Recommendation Engine
    └── Job Queue (Celery)

Data Storage
    ├── MongoDB (primary data)
    ├── Redis (cache, queue)
    └── S3 (screenshots, exports)
```

---

## REST API ENDPOINTS

### 1. AUDIT ENDPOINTS

#### 1.1 Start Page Audit

```
POST /api/v1/audit/page
```

**Purpose**: Initiate a single-page AEO audit

**Request Body**:
```json
{
  "url": "https://example.com/page",
  "options": {
    "include_ai_citation": true,
    "ai_prompt_count": 20,
    "ai_engines": ["gpt4", "gemini", "perplexity"],
    "wait_for_completion": false,
    "priority": "normal"
  }
}
```

**Response** (202 Accepted):
```json
{
  "job_id": "job_abc123xyz",
  "status": "queued",
  "url": "https://example.com/page",
  "estimated_completion": "2024-11-26T10:05:00Z",
  "status_url": "/api/v1/jobs/job_abc123xyz"
}
```

**Response** (if wait_for_completion=true, 200 OK):
```json
{
  "job_id": "job_abc123xyz",
  "status": "completed",
  "url": "https://example.com/page",
  "result": {
    "overall_score": 78.5,
    "grade": "B+",
    "breakdown": {...},
    "recommendations": {...}
  },
  "completed_at": "2024-11-26T10:03:45Z"
}
```

---

#### 1.2 Start Domain Audit

```
POST /api/v1/audit/domain
```

**Purpose**: Audit entire domain (crawl and score multiple pages)

**Request Body**:
```json
{
  "domain": "example.com",
  "options": {
    "max_pages": 50,
    "include_subdomains": false,
    "crawl_depth": 3,
    "include_ai_citation": false,
    "page_filter": {
      "include_patterns": ["/blog/", "/guides/"],
      "exclude_patterns": ["/admin/", "/api/"]
    }
  }
}
```

**Response** (202 Accepted):
```json
{
  "job_id": "job_domain_xyz789",
  "status": "queued",
  "domain": "example.com",
  "estimated_pages": 50,
  "estimated_completion": "2024-11-26T11:00:00Z",
  "status_url": "/api/v1/jobs/job_domain_xyz789"
}
```

---

### 2. SCORE ENDPOINTS

#### 2.1 Get Page Score

```
GET /api/v1/scores/page?url=https://example.com/page
```

**Response** (200 OK):
```json
{
  "url": "https://example.com/page",
  "audit_id": "audit_123",
  "audited_at": "2024-11-26T10:00:00Z",
  "overall_score": 78.5,
  "grade": "B+",
  "breakdown": {
    "answerability": {
      "score": 24,
      "max": 30,
      "percentage": 80,
      "sub_scores": {
        "direct_answer_presence": 10,
        "question_coverage": 6,
        "answer_conciseness": 5,
        "answer_block_formatting": 3
      }
    },
    "structured_data": {
      "score": 14,
      "max": 20,
      "percentage": 70,
      "sub_scores": {...}
    },
    "authority": {...},
    "content_quality": {...},
    "citationability": {...},
    "technical": {...},
    "ai_citation": {...}
  },
  "historical_scores": [
    {"date": "2024-11-20", "score": 75.0},
    {"date": "2024-11-26", "score": 78.5}
  ]
}
```

---

#### 2.2 Get Domain Scores

```
GET /api/v1/scores/domain?domain=example.com
```

**Response** (200 OK):
```json
{
  "domain": "example.com",
  "overview": {
    "total_pages": 45,
    "avg_score": 76.3,
    "median_score": 78.0,
    "score_distribution": {
      "A": 5,
      "B": 25,
      "C": 10,
      "D": 3,
      "F": 2
    }
  },
  "pages": [
    {
      "url": "https://example.com/page1",
      "score": 85.0,
      "grade": "A",
      "audited_at": "2024-11-26T10:00:00Z"
    },
    {
      "url": "https://example.com/page2",
      "score": 78.5,
      "grade": "B+",
      "audited_at": "2024-11-26T10:05:00Z"
    }
  ],
  "top_pages": [...],
  "bottom_pages": [...]
}
```

---

### 3. RECOMMENDATION ENDPOINTS

#### 3.1 Get Recommendations

```
GET /api/v1/recommendations?url=https://example.com/page
```

**Response** (200 OK):
```json
{
  "url": "https://example.com/page",
  "generated_at": "2024-11-26T10:00:00Z",
  "total_recommendations": 12,
  "summary": {
    "by_severity": {
      "critical": 1,
      "high": 3,
      "medium": 6,
      "low": 2
    },
    "by_category": {
      "answerability": 3,
      "structured_data": 4,
      "authority": 2,
      "content_quality": 2,
      "technical": 1
    },
    "potential_score_gain": 18.5,
    "estimated_total_time": "3 hours"
  },
  "quick_wins": [
    {
      "id": "rec_001",
      "title": "Add TL;DR Summary Block",
      "priority": 85,
      "impact": "+6.0 points",
      "effort": "Easy",
      "estimated_time": "15 minutes",
      "severity": "medium"
    }
  ],
  "recommendations": [
    {
      "id": "rec_001",
      "title": "Add TL;DR Summary Block",
      "category": "answerability",
      "subcategory": "answer_conciseness",
      "priority": 85,
      "impact": 6.0,
      "effort": "Easy",
      "severity": "medium",
      "description": "Add a TL;DR (Too Long; Didn't Read) summary...",
      "explanation": "A TL;DR provides a scannable summary...",
      "how_to_fix": [
        "Write a 2-4 sentence summary of your main points",
        "Place it prominently near the top (after intro)",
        "Use visual formatting to make it stand out"
      ],
      "current_state": {"tldr_section": "Missing"},
      "desired_state": {"tldr_section": "Present"},
      "code_snippet": "<div class=\"tldr-box\">...</div>",
      "before_example": "...",
      "after_example": "...",
      "estimated_time": "15 minutes",
      "resources": [
        "https://www.nngroup.com/articles/blah-blah-text/"
      ],
      "tags": ["content", "formatting", "quick-win"]
    }
  ]
}
```

---

#### 3.2 Mark Recommendation as Implemented

```
POST /api/v1/recommendations/{rec_id}/implement
```

**Request Body**:
```json
{
  "url": "https://example.com/page",
  "implemented_at": "2024-11-26T12:00:00Z",
  "notes": "Added TL;DR section at top of article"
}
```

**Response** (200 OK):
```json
{
  "recommendation_id": "rec_001",
  "status": "implemented",
  "reaudit_scheduled": true,
  "reaudit_job_id": "job_reaudit_123"
}
```

---

### 4. DOMAIN MANAGEMENT ENDPOINTS

#### 4.1 Register Domain

```
POST /api/v1/domains
```

**Request Body**:
```json
{
  "domain": "example.com",
  "name": "My Blog",
  "owner_email": "owner@example.com",
  "audit_schedule": {
    "enabled": true,
    "frequency": "weekly",
    "day_of_week": "monday",
    "time": "09:00"
  }
}
```

**Response** (201 Created):
```json
{
  "domain_id": "dom_123",
  "domain": "example.com",
  "created_at": "2024-11-26T10:00:00Z",
  "next_audit": "2024-12-02T09:00:00Z"
}
```

---

#### 4.2 Get Domain Details

```
GET /api/v1/domains/{domain_id}
```

**Response** (200 OK):
```json
{
  "domain_id": "dom_123",
  "domain": "example.com",
  "name": "My Blog",
  "owner_email": "owner@example.com",
  "created_at": "2024-11-26T10:00:00Z",
  "stats": {
    "total_audits": 15,
    "last_audit": "2024-11-26T10:00:00Z",
    "avg_score": 76.3,
    "avg_score_trend": "+2.5"
  },
  "audit_schedule": {...}
}
```

---

#### 4.3 List All Domains

```
GET /api/v1/domains?limit=50&offset=0
```

**Response** (200 OK):
```json
{
  "total": 125,
  "limit": 50,
  "offset": 0,
  "domains": [
    {
      "domain_id": "dom_123",
      "domain": "example.com",
      "avg_score": 76.3,
      "last_audit": "2024-11-26T10:00:00Z"
    }
  ]
}
```

---

### 5. JOB STATUS ENDPOINTS

#### 5.1 Get Job Status

```
GET /api/v1/jobs/{job_id}
```

**Response** (200 OK):
```json
{
  "job_id": "job_abc123xyz",
  "type": "page_audit",
  "status": "processing",
  "progress": {
    "current_step": "ai_citation_evaluation",
    "steps_completed": 5,
    "total_steps": 7,
    "percentage": 71
  },
  "created_at": "2024-11-26T10:00:00Z",
  "started_at": "2024-11-26T10:00:15Z",
  "estimated_completion": "2024-11-26T10:05:00Z",
  "url": "https://example.com/page",
  "result_url": null
}
```

**Response** (when completed):
```json
{
  "job_id": "job_abc123xyz",
  "type": "page_audit",
  "status": "completed",
  "progress": {
    "percentage": 100
  },
  "created_at": "2024-11-26T10:00:00Z",
  "completed_at": "2024-11-26T10:03:45Z",
  "url": "https://example.com/page",
  "result_url": "/api/v1/scores/page?url=https://example.com/page"
}
```

---

#### 5.2 Cancel Job

```
DELETE /api/v1/jobs/{job_id}
```

**Response** (200 OK):
```json
{
  "job_id": "job_abc123xyz",
  "status": "cancelled"
}
```

---

### 6. EXPORT ENDPOINTS

#### 6.1 Export Audit Report

```
GET /api/v1/export/report?url=https://example.com/page&format=pdf
```

**Query Parameters**:
- `url`: Page URL
- `format`: pdf, html, markdown, json
- `include_code_snippets`: true/false
- `sections`: all, scores_only, recommendations_only

**Response** (200 OK):
```json
{
  "export_id": "exp_123",
  "format": "pdf",
  "download_url": "https://storage.example.com/exports/exp_123.pdf",
  "expires_at": "2024-11-27T10:00:00Z"
}
```

---

#### 6.2 Export Domain Dashboard

```
GET /api/v1/export/dashboard?domain=example.com&format=csv
```

**Response** (200 OK):
```json
{
  "export_id": "exp_456",
  "format": "csv",
  "download_url": "https://storage.example.com/exports/exp_456.csv",
  "expires_at": "2024-11-27T10:00:00Z"
}
```

---

## DATABASE SCHEMAS

### MongoDB Collections

#### 1. audits

**Purpose**: Store complete audit results

```json
{
  "_id": "audit_123",
  "url": "https://example.com/page",
  "domain": "example.com",
  "status": "completed",
  "created_at": "2024-11-26T10:00:00Z",
  "completed_at": "2024-11-26T10:03:45Z",
  "execution_time_ms": 225000,
  
  "extracted_data": {
    "title": "Complete Guide to AEO",
    "meta_description": "...",
    "word_count": 2500,
    "headings": [...],
    "questions": [...],
    "jsonld": [...],
    "author": {...},
    "performance": {...}
  },
  
  "scores": {
    "overall_score": 78.5,
    "grade": "B+",
    "breakdown": {
      "answerability": {
        "score": 24,
        "max": 30,
        "sub_scores": {
          "direct_answer_presence": 10,
          "question_coverage": 6,
          "answer_conciseness": 5,
          "answer_block_formatting": 3
        }
      },
      "structured_data": {...},
      "authority": {...},
      "content_quality": {...},
      "citationability": {...},
      "technical": {...},
      "ai_citation": {...}
    }
  },
  
  "gaps": [
    {
      "category": "answerability",
      "subcategory": "answer_conciseness",
      "gap_size": 1,
      "severity": "medium"
    }
  ],
  
  "recommendations": [
    {
      "id": "rec_001",
      "title": "Add TL;DR Summary Block",
      "priority": 85,
      "status": "pending",
      "category": "answerability"
    }
  ],
  
  "ai_citation_data": {
    "evaluated": true,
    "prompt_count": 20,
    "engines_used": ["gpt4", "gemini", "perplexity"],
    "citation_rate": 0.15,
    "avg_similarity": 0.72,
    "evidence": [...]
  },
  
  "metadata": {
    "user_agent": "AEOScoreBot/1.0",
    "crawler_version": "1.0.0",
    "ip_address": "1.2.3.4"
  }
}
```

**Indexes**:
```javascript
db.audits.createIndex({ "url": 1, "created_at": -1 })
db.audits.createIndex({ "domain": 1, "created_at": -1 })
db.audits.createIndex({ "status": 1, "created_at": -1 })
db.audits.createIndex({ "scores.overall_score": -1 })
```

---

#### 2. domains

**Purpose**: Manage domains and their audit schedules

```json
{
  "_id": "dom_123",
  "domain": "example.com",
  "name": "My Blog",
  "owner_email": "owner@example.com",
  "created_at": "2024-11-26T10:00:00Z",
  "updated_at": "2024-11-26T10:00:00Z",
  
  "audit_schedule": {
    "enabled": true,
    "frequency": "weekly",
    "day_of_week": "monday",
    "time": "09:00",
    "timezone": "UTC"
  },
  
  "crawl_config": {
    "max_pages": 50,
    "include_subdomains": false,
    "crawl_depth": 3,
    "page_filter": {
      "include_patterns": ["/blog/", "/guides/"],
      "exclude_patterns": ["/admin/", "/api/"]
    }
  },
  
  "stats": {
    "total_audits": 15,
    "total_pages_audited": 450,
    "last_audit_id": "audit_xyz",
    "last_audit_date": "2024-11-26T10:00:00Z",
    "avg_score": 76.3,
    "avg_score_trend": "+2.5"
  },
  
  "settings": {
    "notifications": {
      "enabled": true,
      "email": "owner@example.com",
      "slack_webhook": null
    }
  }
}
```

**Indexes**:
```javascript
db.domains.createIndex({ "domain": 1 }, { unique: true })
db.domains.createIndex({ "owner_email": 1 })
db.domains.createIndex({ "audit_schedule.enabled": 1, "audit_schedule.frequency": 1 })
```

---

#### 3. jobs

**Purpose**: Track async job status

```json
{
  "_id": "job_abc123xyz",
  "type": "page_audit",
  "status": "processing",
  "priority": "normal",
  "created_at": "2024-11-26T10:00:00Z",
  "started_at": "2024-11-26T10:00:15Z",
  "completed_at": null,
  "expires_at": "2024-11-27T10:00:00Z",
  
  "input": {
    "url": "https://example.com/page",
    "options": {
      "include_ai_citation": true,
      "ai_prompt_count": 20
    }
  },
  
  "progress": {
    "current_step": "ai_citation_evaluation",
    "steps_completed": 5,
    "total_steps": 7,
    "percentage": 71,
    "messages": [
      "Fetching page...",
      "Extracting content...",
      "Analyzing structure...",
      "Computing scores...",
      "Evaluating AI citations..."
    ]
  },
  
  "result": {
    "audit_id": "audit_123",
    "url": "/api/v1/scores/page?url=https://example.com/page"
  },
  
  "error": null,
  "retry_count": 0,
  "max_retries": 3
}
```

**Indexes**:
```javascript
db.jobs.createIndex({ "status": 1, "created_at": -1 })
db.jobs.createIndex({ "expires_at": 1 }, { expireAfterSeconds: 0 })
db.jobs.createIndex({ "_id": 1, "status": 1 })
```

---

#### 4. recommendations_history

**Purpose**: Track implementation of recommendations

```json
{
  "_id": "rec_hist_123",
  "recommendation_id": "rec_001",
  "audit_id": "audit_123",
  "url": "https://example.com/page",
  "domain": "example.com",
  
  "recommendation": {
    "title": "Add TL;DR Summary Block",
    "category": "answerability",
    "priority": 85,
    "impact": 6.0
  },
  
  "status": "implemented",
  "implemented_at": "2024-11-26T12:00:00Z",
  "implemented_by": "user_123",
  "notes": "Added TL;DR section at top of article",
  
  "impact_measurement": {
    "before_score": 78.5,
    "after_score": 82.3,
    "actual_gain": 3.8,
    "reaudit_id": "audit_456",
    "verified": true
  },
  
  "created_at": "2024-11-26T10:00:00Z",
  "updated_at": "2024-11-26T13:00:00Z"
}
```

**Indexes**:
```javascript
db.recommendations_history.createIndex({ "url": 1, "status": 1 })
db.recommendations_history.createIndex({ "domain": 1, "implemented_at": -1 })
db.recommendations_history.createIndex({ "audit_id": 1 })
```

---

#### 5. ai_citation_cache

**Purpose**: Cache AI engine responses to avoid redundant API calls

```json
{
  "_id": "cache_123",
  "prompt_hash": "sha256_hash_of_prompt",
  "engine": "gpt4",
  "prompt": "What is AEO?",
  "response": "Answer Engine Optimization...",
  "citations": ["https://example.com/aeo-guide"],
  "cached_at": "2024-11-26T10:00:00Z",
  "ttl": 604800,
  "expires_at": "2024-12-03T10:00:00Z"
}
```

**Indexes**:
```javascript
db.ai_citation_cache.createIndex({ "prompt_hash": 1, "engine": 1 }, { unique: true })
db.ai_citation_cache.createIndex({ "expires_at": 1 }, { expireAfterSeconds: 0 })
```

---

### Redis Data Structures

#### 1. Job Queue

```
LIST aeo:queue:high_priority
LIST aeo:queue:normal_priority
LIST aeo:queue:low_priority
```

**Job Entry** (JSON string):
```json
{
  "job_id": "job_abc123xyz",
  "type": "page_audit",
  "url": "https://example.com/page",
  "options": {...}
}
```

---

#### 2. Score Cache

```
KEY: aeo:score:{url_hash}
VALUE: JSON string of score data
TTL: 3600 (1 hour)
```

---

#### 3. Rate Limiting

```
KEY: aeo:ratelimit:{api_key}:{endpoint}
VALUE: request count
TTL: 60 (1 minute)
```

---

## API CLIENT EXAMPLES

### Python Client

```python
import requests

class AEOClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    def audit_page(self, url: str, wait: bool = False):
        """Start page audit"""
        response = requests.post(
            f'{self.base_url}/api/v1/audit/page',
            headers=self.headers,
            json={
                'url': url,
                'options': {'wait_for_completion': wait}
            }
        )
        return response.json()
    
    def get_score(self, url: str):
        """Get page score"""
        response = requests.get(
            f'{self.base_url}/api/v1/scores/page',
            headers=self.headers,
            params={'url': url}
        )
        return response.json()
    
    def get_recommendations(self, url: str):
        """Get recommendations"""
        response = requests.get(
            f'{self.base_url}/api/v1/recommendations',
            headers=self.headers,
            params={'url': url}
        )
        return response.json()

# Usage
client = AEOClient('https://api.aeoscore.com', 'your_api_key')
result = client.audit_page('https://example.com/page', wait=True)
print(f"Score: {result['result']['overall_score']}")
```

---

### JavaScript Client

```javascript
class AEOClient {
  constructor(baseURL, apiKey) {
    this.baseURL = baseURL;
    this.apiKey = apiKey;
  }

  async auditPage(url, wait = false) {
    const response = await fetch(`${this.baseURL}/api/v1/audit/page`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        url: url,
        options: { wait_for_completion: wait }
      })
    });
    return await response.json();
  }

  async getScore(url) {
    const response = await fetch(
      `${this.baseURL}/api/v1/scores/page?url=${encodeURIComponent(url)}`,
      {
        headers: { 'Authorization': `Bearer ${this.apiKey}` }
      }
    );
    return await response.json();
  }

  async getRecommendations(url) {
    const response = await fetch(
      `${this.baseURL}/api/v1/recommendations?url=${encodeURIComponent(url)}`,
      {
        headers: { 'Authorization': `Bearer ${this.apiKey}` }
      }
    );
    return await response.json();
  }
}

// Usage
const client = new AEOClient('https://api.aeoscore.com', 'your_api_key');
const result = await client.auditPage('https://example.com/page', true);
console.log(`Score: ${result.result.overall_score}`);
```

---

## AUTHENTICATION & RATE LIMITING

### Authentication

**Method**: Bearer Token (JWT)

**Request Header**:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Rate Limits**:
```
Free Tier:    10 audits/day,   100 API calls/hour
Pro Tier:     100 audits/day,  1000 API calls/hour
Enterprise:   Unlimited
```

**Rate Limit Headers**:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1732616400
```

---

## ERROR RESPONSES

### Standard Error Format

```json
{
  "error": {
    "code": "INVALID_URL",
    "message": "The provided URL is not accessible",
    "details": {
      "url": "https://example.com/page",
      "status_code": 404
    },
    "request_id": "req_abc123"
  }
}
```

### Error Codes

```
400 BAD_REQUEST
  - INVALID_URL: URL is malformed or not accessible
  - MISSING_PARAMETER: Required parameter missing
  - INVALID_OPTION: Invalid option value

401 UNAUTHORIZED
  - INVALID_TOKEN: API key invalid or expired
  - TOKEN_REQUIRED: No authentication provided

403 FORBIDDEN
  - RATE_LIMIT_EXCEEDED: Too many requests
  - INSUFFICIENT_PERMISSIONS: Action not allowed

404 NOT_FOUND
  - RESOURCE_NOT_FOUND: Requested resource doesn't exist
  - AUDIT_NOT_FOUND: Audit ID not found

429 TOO_MANY_REQUESTS
  - RATE_LIMIT_EXCEEDED: Rate limit hit

500 INTERNAL_SERVER_ERROR
  - CRAWLER_ERROR: Crawler failed
  - SCORING_ERROR: Scoring engine failed
  - DATABASE_ERROR: Database operation failed

503 SERVICE_UNAVAILABLE
  - QUEUE_FULL: Job queue at capacity
  - MAINTENANCE_MODE: System under maintenance
```

---

## WEBHOOKS

### Configure Webhook

```
POST /api/v1/webhooks
```

**Request**:
```json
{
  "url": "https://yoursite.com/webhook",
  "events": ["audit.completed", "audit.failed"],
  "secret": "your_webhook_secret"
}
```

### Webhook Payload (audit.completed)

```json
{
  "event": "audit.completed",
  "timestamp": "2024-11-26T10:03:45Z",
  "data": {
    "audit_id": "audit_123",
    "url": "https://example.com/page",
    "overall_score": 78.5,
    "grade": "B+",
    "result_url": "/api/v1/scores/page?url=https://example.com/page"
  },
  "signature": "sha256_hmac_signature"
}
```

---

## NEXT STEPS
- Frontend specifications to consume these APIs
- Implementation code (FastAPI backend)
- Testing suite for APIs

