"""
Audit API endpoints
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from loguru import logger
import uuid
from datetime import datetime

router = APIRouter()


class AuditOptions(BaseModel):
    """Audit configuration options"""
    include_ai_citation: bool = True
    ai_prompt_count: int = 20
    ai_engines: List[str] = ["gpt4", "gemini", "perplexity"]
    wait_for_completion: bool = False
    priority: str = "normal"


class PageAuditRequest(BaseModel):
    """Request to audit a single page"""
    url: HttpUrl
    deep_crawl: bool = False  # For backward compatibility with frontend
    re_audit: bool = False  # For backward compatibility with frontend
    options: Optional[AuditOptions] = None


class DomainAuditRequest(BaseModel):
    """Request to audit entire domain"""
    domain: str
    options: Optional[dict] = None


class AuditResponse(BaseModel):
    """Response from audit submission"""
    job_id: str
    status: str
    url: str
    estimated_completion: Optional[str] = None
    status_url: str


@router.post("/page")
async def audit_page(request: PageAuditRequest, background_tasks: BackgroundTasks):
    """
    Start a single-page AEO audit
    
    Args:
        request: Audit request with URL and options
        background_tasks: FastAPI background tasks
        
    Returns:
        Job information with complete audit results (runs synchronously for MVP)
    """
    logger.info(f"Received audit request for: {request.url}")
    
    # Generate job ID
    job_id = f"job_{uuid.uuid4().hex[:12]}"
    
    # Use default options if not provided
    options = request.options if request.options else AuditOptions()
    
    # For MVP, always run synchronously and return complete results
    result = await _execute_audit(str(request.url), options)
    
    return {
        "job_id": job_id,
        "status": "completed",
        "url": str(request.url),
        "status_url": f"/api/v1/jobs/{job_id}",
        "result": result,
        "completed_at": datetime.utcnow().isoformat()
    }


@router.post("/domain", response_model=AuditResponse)
async def audit_domain(request: DomainAuditRequest):
    """
    Start a domain-wide AEO audit
    
    Args:
        request: Domain audit request
        
    Returns:
        Job information
    """
    logger.info(f"Received domain audit request for: {request.domain}")
    
    # Generate job ID
    job_id = f"job_domain_{uuid.uuid4().hex[:12]}"
    
    # TODO: Implement domain crawling and auditing
    
    return AuditResponse(
        job_id=job_id,
        status="queued",
        url=f"https://{request.domain}",
        estimated_completion=None,
        status_url=f"/api/v1/jobs/{job_id}"
    )


async def _execute_audit(url: str, options: AuditOptions) -> dict:
    """
    Execute the audit using the real pipeline
    
    Steps:
    1. Fetch page with crawler
    2. Extract data
    3. Calculate scores
    4. Generate recommendations
    5. If enabled, run AI citation analysis (TODO)
    """
    logger.info(f"Executing real audit for {url}")
    
    try:
        # Import here to avoid circular imports
        from audit_pipeline import AuditPipeline
        
        pipeline = AuditPipeline()
        result = await pipeline.audit_page(url, options.dict())
        
        return result
        
    except Exception as e:
        logger.error(f"Audit failed: {e}")
        # Return error with details
        return {
            "overall_score": 0,
            "grade": "F",
            "error": str(e),
            "breakdown": {}
        }

