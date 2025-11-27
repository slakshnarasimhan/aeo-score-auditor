"""
FastAPI application entry point
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
import time

from config import settings
from api.routes import audit, scores, recommendations, domains, jobs

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AEO Score Auditor API",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
)

# CORS middleware - allow all origins for network access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for network sharing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url}")
    
    # Process request
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} in {process_time:.2f}s")
    
    # Add process time header
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "details": str(exc) if settings.DEBUG else None
            }
        }
    )


# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }


# Include routers
app.include_router(audit.router, prefix=f"{settings.API_PREFIX}/audit", tags=["Audit"])
app.include_router(scores.router, prefix=f"{settings.API_PREFIX}/scores", tags=["Scores"])
app.include_router(recommendations.router, prefix=f"{settings.API_PREFIX}/recommendations", tags=["Recommendations"])
app.include_router(domains.router, prefix=f"{settings.API_PREFIX}/domains", tags=["Domains"])
app.include_router(jobs.router, prefix=f"{settings.API_PREFIX}/jobs", tags=["Jobs"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )

