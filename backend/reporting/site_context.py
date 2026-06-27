"""
Supplemental per-site context loading.
"""
import json
import os
import re
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urlparse

try:
    from loguru import logger
except Exception:
    import logging

    logger = logging.getLogger(__name__)


REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = Path(os.getenv("AEO_DATA_DIR", REPO_ROOT / "domains")).expanduser()
SITE_CONTEXT_DIR = DATA_ROOT / "site_context"


def load_site_context(site_url: str, explicit_context: Any = None) -> Dict[str, Any]:
    """Load explicit or per-domain supplemental context.

    Explicit context can be a dict or a JSON file path. If absent, this looks
    for domains/site_context/<domain>.json. Missing context intentionally returns an
    empty dict; positioning then defaults to global.
    """
    if isinstance(explicit_context, dict):
        payload = dict(explicit_context)
        payload["_context_path"] = "request_options"
        return payload

    if isinstance(explicit_context, str) and explicit_context.strip():
        path = Path(explicit_context).expanduser()
        if not path.is_absolute():
            repo_path = REPO_ROOT / path
            data_path = DATA_ROOT / path
            path = repo_path if repo_path.exists() else data_path
        loaded = _read_context(path)
        if loaded:
            return loaded

    context_path = SITE_CONTEXT_DIR / f"{_domain_key(site_url)}.json"
    return _read_context(context_path)


def _read_context(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning(f"Failed to load site context from {path}: {e}")
        return {}
    if not isinstance(payload, dict):
        logger.warning(f"Site context must be a JSON object: {path}")
        return {}
    payload["_context_path"] = str(path)
    return payload


def _domain_key(site_url: str) -> str:
    parsed = urlparse(site_url if "://" in site_url else f"https://{site_url}")
    host = parsed.netloc or parsed.path.split("/")[0] or "site"
    host = host.replace("www.", "")
    return re.sub(r"[^a-zA-Z0-9._-]+", "-", host).strip("-._") or "site"
