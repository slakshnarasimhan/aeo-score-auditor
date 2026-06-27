"""
Local crawl persistence for audit debugging and reuse.
"""
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlparse

try:
    from loguru import logger
except Exception:
    import logging

    logger = logging.getLogger(__name__)


REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = Path(os.getenv("AEO_DATA_DIR", REPO_ROOT / "domains")).expanduser()
CRAWL_ROOT = DATA_ROOT / "crawls"


def persist_page_extraction(url: str, extracted_data: Dict[str, Any]) -> str:
    """Persist the full extracted page payload under domains/crawls."""
    domain_dir = _domain_dir(url)
    page_dir = domain_dir / "pages"
    page_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "url": url,
        "persisted_at": datetime.utcnow().isoformat(),
        "extracted_data": extracted_data,
    }
    page_key = _page_key(url)
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    path = page_dir / f"{page_key}-{timestamp}.json"
    latest_path = page_dir / f"{page_key}-latest.json"

    _write_json(path, payload)
    _write_json(latest_path, payload)
    _update_index(url, str(latest_path), payload["persisted_at"])
    logger.debug(f"Persisted page extraction for {url} to {path}")
    return str(path)


def load_page_extraction(url: str) -> Dict[str, Any]:
    """Load the latest persisted extracted page payload for a URL."""
    domain_dir = _domain_dir(url)
    index = _read_json(domain_dir / "index.json")
    page_record = (index.get("pages") or {}).get(url)
    if page_record:
        path = Path(page_record.get("latest_path", ""))
        if path.exists():
            payload = _read_json(path)
            extracted = payload.get("extracted_data")
            if isinstance(extracted, dict):
                return extracted

    latest_path = domain_dir / "pages" / f"{_page_key(url)}-latest.json"
    if latest_path.exists():
        payload = _read_json(latest_path)
        extracted = payload.get("extracted_data")
        if isinstance(extracted, dict):
            return extracted

    raise FileNotFoundError(
        f"No local crawl found for {url}. Run a normal crawl first."
    )


def latest_page_artifact_path(url: str) -> str:
    """Return the latest persisted artifact path for a URL, if known."""
    domain_dir = _domain_dir(url)
    index = _read_json(domain_dir / "index.json")
    page_record = (index.get("pages") or {}).get(url)
    if page_record and page_record.get("latest_path"):
        return str(page_record["latest_path"])
    latest_path = domain_dir / "pages" / f"{_page_key(url)}-latest.json"
    return str(latest_path) if latest_path.exists() else ""


def list_cached_urls(domain_url: str) -> List[str]:
    """Return URLs available in the local crawl cache for a domain."""
    domain_dir = _domain_dir(domain_url)
    index = _read_json(domain_dir / "index.json")
    pages = index.get("pages") or {}
    urls = list(pages.keys())
    latest_audit = _read_json(domain_dir / "latest-domain-audit.json")
    discovered = latest_audit.get("discovered_urls") or []
    for url in discovered:
        if isinstance(url, str) and url not in urls:
            urls.append(url)
    return urls


def build_cached_domain_evidence(
    domain_url: str,
    max_pages: int = 12,
    max_chars: int = 24000,
) -> str:
    """Build a compact evidence packet from persisted page extractions."""
    sections: List[str] = []
    total_chars = 0
    for url in list_cached_urls(domain_url)[:max_pages]:
        try:
            data = load_page_extraction(url)
        except FileNotFoundError:
            continue

        headings = [
            str(item.get("text", "")).strip()
            for item in data.get("headings", [])[:12]
            if isinstance(item, dict) and item.get("text")
        ]
        paragraphs = [
            str(item.get("text", "")).strip()
            for item in data.get("paragraphs", [])[:5]
            if isinstance(item, dict) and item.get("text")
        ]
        section = "\n".join(
            line for line in [
                f"URL: {url}",
                f"Title: {data.get('title', '')}",
                f"Description: {data.get('meta_description', '')}",
                f"Headings: {' | '.join(headings)}",
                f"Page text: {' '.join(paragraphs)}",
            ] if line.split(":", 1)[-1].strip()
        )
        remaining = max_chars - total_chars
        if remaining <= 0:
            break
        sections.append(section[:remaining])
        total_chars += len(sections[-1])
    return "\n\n---\n\n".join(sections)


def build_page_results_evidence(
    page_results: List[Dict[str, Any]],
    max_pages: int = 15,
    max_chars: int = 30000,
) -> str:
    """Build a strategy evidence packet from already-audited page results."""
    sections: List[str] = []
    total_chars = 0
    for result in page_results[:max_pages]:
        evidence = result.get("prompt_evidence") or {}
        section = "\n".join(
            line for line in [
                f"URL: {result.get('url', '')}",
                f"Title: {evidence.get('title', '')}",
                f"Description: {evidence.get('meta_description', '')}",
                f"Headings: {' | '.join(evidence.get('headings', [])[:15])}",
                f"Page text: {' '.join(evidence.get('paragraphs', [])[:6])}",
                f"Questions found: {json.dumps(evidence.get('questions', [])[:8], default=str)}",
            ] if line.split(":", 1)[-1].strip()
        )
        remaining = max_chars - total_chars
        if remaining <= 0:
            break
        sections.append(section[:remaining])
        total_chars += len(sections[-1])
    return "\n\n---\n\n".join(sections)


def persist_domain_audit(
    domain_url: str,
    job_id: str | None,
    discovered_urls: list[str],
    page_results: list[Dict[str, Any]],
    aggregated_result: Dict[str, Any],
) -> str:
    """Persist discovered URLs and aggregate domain audit results."""
    domain_dir = _domain_dir(domain_url)
    domain_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "domain": domain_url,
        "job_id": job_id,
        "persisted_at": datetime.utcnow().isoformat(),
        "discovered_urls": discovered_urls,
        "page_results": page_results,
        "aggregated_result": aggregated_result,
    }
    run_key = job_id or datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    path = domain_dir / f"audit-{_safe_name(run_key)}.json"
    latest_path = domain_dir / "latest-domain-audit.json"

    _write_json(path, payload)
    _write_json(latest_path, payload)
    logger.info(f"Persisted domain audit for {domain_url} to {path}")
    return str(path)


def _update_index(url: str, latest_path: str, persisted_at: str) -> None:
    domain_dir = _domain_dir(url)
    index_path = domain_dir / "index.json"
    index = _read_json(index_path)
    parsed = urlparse(url if "://" in url else f"https://{url}")
    host = parsed.netloc or parsed.path.split("/")[0] or "local"
    pages = index.get("pages") if isinstance(index.get("pages"), dict) else {}
    pages[url] = {
        "latest_path": latest_path,
        "page_key": _page_key(url),
        "persisted_at": persisted_at,
    }
    index.update({
        "domain": host.replace("www.", ""),
        "updated_at": persisted_at,
        "pages": pages,
    })
    _write_json(index_path, index)


def _domain_dir(url: str) -> Path:
    parsed = urlparse(url if "://" in url else f"https://{url}")
    host = parsed.netloc or parsed.path.split("/")[0] or "local"
    return CRAWL_ROOT / _safe_name(host.replace("www.", ""))


def _page_key(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.strip("/") or "home"
    if parsed.query:
        path = f"{path}-{parsed.query}"
    return _safe_name(path)[:120] or "page"


def _safe_name(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip("-._")
    return cleaned or "item"


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning(f"Failed to read crawl cache {path}: {e}")
        return {}
    return payload if isinstance(payload, dict) else {}
