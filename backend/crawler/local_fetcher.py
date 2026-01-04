"""
Local file fetcher for auditing HTML files from disk
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from loguru import logger
import time


@dataclass
class PageData:
    """Page data structure"""
    html: str
    status_code: int
    url: str
    error: Optional[str] = None
    performance: dict = None
    
    def __post_init__(self):
        if self.performance is None:
            self.performance = {}


class LocalFileFetcher:
    """Fetches HTML content from local files"""
    
    def __init__(self):
        logger.info("LocalFileFetcher initialized")
    
    async def fetch(self, file_path: str) -> PageData:
        """
        Read HTML from a local file
        
        Args:
            file_path: Path to local HTML file (can be file:// URL or absolute path)
            
        Returns:
            PageData with HTML content
        """
        # Strip file:// prefix if present
        if file_path.startswith('file://'):
            file_path = file_path[7:]  # Remove 'file://'
        
        logger.info(f"Reading local file: {file_path}")
        
        try:
            path = Path(file_path)
            
            if not path.exists():
                error_msg = f"File not found: {file_path}"
                logger.error(error_msg)
                return PageData(
                    html="",
                    status_code=404,
                    url=file_path,
                    error=error_msg
                )
            
            if not path.is_file():
                error_msg = f"Path is not a file: {file_path}"
                logger.error(error_msg)
                return PageData(
                    html="",
                    status_code=400,
                    url=file_path,
                    error=error_msg
                )
            
            # Read file
            start_time = time.time()
            html_content = path.read_text(encoding='utf-8')
            read_time = (time.time() - start_time) * 1000  # ms
            
            logger.success(f"Successfully read {len(html_content)} bytes from {file_path}")
            
            return PageData(
                html=html_content,
                status_code=200,
                url=f"file://{path.absolute()}",
                performance={
                    'ttfb': read_time,
                    'load_time': read_time,
                    'size_bytes': len(html_content),
                    'is_local_file': True
                }
            )
            
        except UnicodeDecodeError as e:
            error_msg = f"Failed to decode file as UTF-8: {e}"
            logger.error(error_msg)
            return PageData(
                html="",
                status_code=500,
                url=file_path,
                error=error_msg
            )
        except Exception as e:
            error_msg = f"Failed to read file: {e}"
            logger.error(error_msg)
            return PageData(
                html="",
                status_code=500,
                url=file_path,
                error=error_msg
            )

