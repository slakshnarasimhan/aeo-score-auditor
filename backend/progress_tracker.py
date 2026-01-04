"""
Progress tracking for long-running domain audits
"""
import asyncio
from typing import Dict, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict, field
import json


@dataclass
class ProgressUpdate:
    """Progress update data"""
    job_id: str
    status: str  # discovering, auditing, completed, failed
    current_step: str
    total_urls: int
    urls_discovered: int
    pages_audited: int
    current_url: Optional[str] = None
    percentage: float = 0.0
    message: str = ""
    timestamp: str = ""
    result: Optional[Any] = None  # Store final result
    
    def to_dict(self):
        data = {}
        for key, value in asdict(self).items():
            if key == 'result' and self.status not in ["completed", "failed"]:
                # Don't include result in regular progress updates
                continue
            data[key] = value
        return data
    
    def to_json(self):
        return json.dumps(self.to_dict(), default=str)


class ProgressTracker:
    """Track progress of domain audits"""
    
    def __init__(self):
        self._progress: Dict[str, ProgressUpdate] = {}
        self._listeners: Dict[str, list] = {}
        self._results: Dict[str, Any] = {}  # Separate storage for results
    
    def create_job(self, job_id: str, total_urls: int = 0):
        """Initialize a new job"""
        self._progress[job_id] = ProgressUpdate(
            job_id=job_id,
            status="discovering",
            current_step="Discovering URLs...",
            total_urls=total_urls,
            urls_discovered=0,
            pages_audited=0,
            percentage=0.0,
            message="Starting domain audit",
            timestamp=datetime.utcnow().isoformat()
        )
        self._listeners[job_id] = []
    
    def update(self, job_id: str, **kwargs):
        """Update job progress"""
        if job_id not in self._progress:
            from loguru import logger
            logger.warning(f"Tried to update non-existent job: {job_id}")
            return
        
        progress = self._progress[job_id]
        
        for key, value in kwargs.items():
            if hasattr(progress, key):
                setattr(progress, key, value)
        
        # Update timestamp
        progress.timestamp = datetime.utcnow().isoformat()
        
        # Calculate percentage
        if progress.total_urls > 0:
            if progress.status == "discovering":
                progress.percentage = min(10, (progress.urls_discovered / max(progress.total_urls, 1)) * 10)
            elif progress.status == "auditing":
                progress.percentage = 10 + ((progress.pages_audited / progress.total_urls) * 90)
            elif progress.status == "completed":
                progress.percentage = 100.0
        
        # Debug logging
        from loguru import logger
        logger.debug(f"Progress update for {job_id}: status={progress.status}, pages={progress.pages_audited}/{progress.total_urls}, percentage={progress.percentage:.1f}%")
        
        # Notify listeners
        self._notify_listeners(job_id)
    
    def get_progress(self, job_id: str) -> Optional[ProgressUpdate]:
        """Get current progress for a job"""
        return self._progress.get(job_id)
    
    def add_listener(self, job_id: str, queue: asyncio.Queue):
        """Add a listener queue for progress updates"""
        if job_id not in self._listeners:
            self._listeners[job_id] = []
        self._listeners[job_id].append(queue)
    
    def remove_listener(self, job_id: str, queue: asyncio.Queue):
        """Remove a listener queue"""
        if job_id in self._listeners:
            if queue in self._listeners[job_id]:
                self._listeners[job_id].remove(queue)
    
    def _notify_listeners(self, job_id: str):
        """Notify all listeners of an update"""
        if job_id not in self._listeners:
            return
        
        progress = self._progress[job_id]
        for queue in self._listeners[job_id]:
            try:
                queue.put_nowait(progress)
            except asyncio.QueueFull:
                pass
    
    def complete_job(self, job_id: str, success: bool = True, message: str = ""):
        """Mark job as completed"""
        self.update(
            job_id,
            status="completed" if success else "failed",
            current_step="Done" if success else "Failed",
            percentage=100.0,
            message=message or ("Audit completed successfully" if success else "Audit failed")
        )
    
    def store_result(self, job_id: str, result: Any):
        """Store result separately for reliable retrieval"""
        self._results[job_id] = result
        # Also attach to progress
        if job_id in self._progress:
            self._progress[job_id].result = result
    
    def get_result(self, job_id: str) -> Optional[Any]:
        """Get stored result"""
        return self._results.get(job_id)
    
    def cleanup(self, job_id: str):
        """Clean up job data"""
        if job_id in self._progress:
            del self._progress[job_id]
        if job_id in self._listeners:
            del self._listeners[job_id]
        if job_id in self._results:
            del self._results[job_id]


# Global progress tracker instance
progress_tracker = ProgressTracker()

