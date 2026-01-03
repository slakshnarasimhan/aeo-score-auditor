"""
Audit API endpoints
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
from loguru import logger
import uuid
from datetime import datetime
import asyncio

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


@router.post("/domain")
async def audit_domain(request: DomainAuditRequest, background_tasks: BackgroundTasks):
    """
    Start a domain-wide AEO audit with progress tracking
    
    Crawls multiple pages from a domain and provides aggregated scores.
    Use /api/v1/audit/domain/progress/{job_id} to track progress.
    
    Args:
        request: Domain audit request
        
    Returns:
        Job information with job_id for progress tracking
    """
    logger.info(f"Received domain audit request for: {request.domain}")
    
    # Generate job ID
    job_id = f"job_domain_{uuid.uuid4().hex[:12]}"
    
    # Ensure domain has scheme
    domain_url = request.domain
    if not domain_url.startswith('http'):
        domain_url = f"https://{domain_url}"
    
    # Get max_pages from options (default: 100, set 0 for unlimited)
    max_pages = 100
    if request.options and 'max_pages' in request.options:
        max_pages = request.options['max_pages']
    
    # Initialize progress tracking
    from progress_tracker import progress_tracker
    progress_tracker.create_job(job_id, total_urls=max_pages)
    
    # Run audit in background
    background_tasks.add_task(_run_domain_audit, job_id, domain_url, max_pages)
    
    return {
        "job_id": job_id,
        "status": "queued",
        "domain": request.domain,
        "progress_url": f"/api/v1/audit/domain/progress/{job_id}",
        "message": "Audit started. Use progress_url to track progress.",
        "estimated_pages": max_pages if max_pages > 0 else "unlimited"
    }


async def _run_domain_audit(job_id: str, domain_url: str, max_pages: int):
    """Background task to run domain audit"""
    try:
        from crawler.domain_crawler import DomainAuditOrchestrator
        from progress_tracker import progress_tracker
        
        orchestrator = DomainAuditOrchestrator(
            max_pages=max_pages,
            max_concurrent=3,
            job_id=job_id
        )
        result = await orchestrator.audit_domain(domain_url)
        
        # Store result in progress tracker (separate storage for reliability)
        progress_tracker.store_result(job_id, result)
        
        logger.info(f"Domain audit completed: {job_id}, result stored")
        logger.debug(f"Result keys: {result.keys() if result else 'None'}")
        
    except Exception as e:
        logger.error(f"Domain audit failed for {job_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        from progress_tracker import progress_tracker
        progress_tracker.complete_job(job_id, success=False, message=str(e))


@router.get("/domain/result/{job_id}")
async def get_domain_result(job_id: str):
    """
    Get completed result for a domain audit job
    
    Args:
        job_id: Job ID from domain audit
        
    Returns:
        Completed audit result
    """
    from progress_tracker import progress_tracker
    
    progress = progress_tracker.get_progress(job_id)
    
    if not progress:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if progress.status not in ["completed", "failed"]:
        raise HTTPException(status_code=400, detail="Job not yet completed")
    
    # Try to get result from separate storage first
    result = progress_tracker.get_result(job_id)
    
    if not result:
        # Fallback to progress.result
        result = progress.result
    
    if not result:
        raise HTTPException(status_code=404, detail="Result not available")
    
    logger.info(f"Returning result for job {job_id}")
    
    return {
        "job_id": job_id,
        "status": progress.status,
        "result": result
    }


@router.get("/domain/progress/{job_id}")
async def get_domain_progress(job_id: str):
    """
    Get progress for a domain audit job (Server-Sent Events)
    
    Args:
        job_id: Job ID from domain audit start
        
    Returns:
        SSE stream with progress updates
    """
    from progress_tracker import progress_tracker
    
    async def event_generator():
        """Generate SSE events"""
        queue = asyncio.Queue()
        progress_tracker.add_listener(job_id, queue)
        
        try:
            # Send initial state
            progress = progress_tracker.get_progress(job_id)
            if progress:
                yield f"data: {progress.to_json()}\n\n"
            
            # Stream updates
            while True:
                try:
                    progress = await asyncio.wait_for(queue.get(), timeout=0.5)
                    yield f"data: {progress.to_json()}\n\n"
                    
                    # If completed or failed, send final result and close
                    if progress.status in ["completed", "failed"]:
                        # Wait a moment for result to be stored
                        await asyncio.sleep(0.3)
                        
                        # Get result from separate storage (more reliable)
                        result = progress_tracker.get_result(job_id)
                        
                        if result:
                            import json
                            result_data = {
                                'status': 'done',
                                'result': result
                            }
                            logger.info(f"Sending final result via SSE for job {job_id}")
                            yield f"data: {json.dumps(result_data, default=str)}\n\n"
                        else:
                            logger.warning(f"Result not found for completed job {job_id}")
                        
                        await asyncio.sleep(0.2)
                        break
                        
                except asyncio.TimeoutError:
                    # Send keep-alive
                    yield f": keep-alive\n\n"
                    
        finally:
            progress_tracker.remove_listener(job_id, queue)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
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


class PDFRequest(BaseModel):
    """Request to generate PDF report"""
    audit_result: Dict[str, Any]
    audit_type: str = "page"  # "page" or "domain"
    detailed: bool = False  # Include all page details in report


@router.post("/pdf")
async def download_pdf_report(request: PDFRequest):
    """
    Generate and download PDF report from audit results
    
    Args:
        request: PDF generation request with audit results
        
    Returns:
        PDF file download
    """
    try:
        from reporting.pdf_generator import generate_pdf_report
        
        logger.info(f"Generating {'detailed' if request.detailed else 'concise'} PDF report for {request.audit_type} audit")
        
        # Generate PDF
        pdf_buffer = generate_pdf_report(request.audit_result, request.audit_type, request.detailed)
        
        # Create filename
        if request.audit_type == 'domain':
            url_part = request.audit_result.get('domain', 'domain').replace('https://', '').replace('http://', '').replace('/', '_')[:30]
        else:
            url_part = request.audit_result.get('url', 'page').replace('https://', '').replace('http://', '').replace('/', '_')[:30]
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"aeo_report_{url_part}_{timestamp}.pdf"
        
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "application/pdf"
            }
        )
        
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")

