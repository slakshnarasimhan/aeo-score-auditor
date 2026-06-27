"""External answer-engine validation for generated AEO questions."""
from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

try:
    from loguru import logger
except Exception:
    import logging

    logger = logging.getLogger(__name__)


def _openai_disabled() -> bool:
    return os.getenv("DISABLE_OPENAI", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = Path(os.getenv("AEO_DATA_DIR", REPO_ROOT / "domains")).expanduser()
AEO_RUN_ROOT = DATA_ROOT / "aeo_runs"


class ExternalAEOValidator:
    """Ask generated questions to external answer engines and score visibility."""

    PROVIDERS = ("openai", "gemini", "grok")

    def __init__(self, providers: List[str] | None = None, max_questions: int | None = None):
        enabled = providers or _env_list("EXTERNAL_AEO_PROVIDERS") or list(self.PROVIDERS)
        if _openai_disabled():
            enabled = [provider for provider in enabled if provider != "openai"]
        self.providers = [item for item in enabled if item in self.PROVIDERS]
        self.max_questions = max_questions or int(os.getenv("EXTERNAL_AEO_MAX_QUESTIONS", "12"))
        self.openai_model = os.getenv("EXTERNAL_AEO_OPENAI_MODEL", "gpt-4o-mini")
        self.gemini_model = os.getenv("EXTERNAL_AEO_GEMINI_MODEL", "gemini-2.5-flash")
        self.grok_model = os.getenv("EXTERNAL_AEO_GROK_MODEL", "grok-4.3")

    def validate(
        self,
        audit_result: Dict[str, Any],
        site_context: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        prompt_analysis = audit_result.get("prompt_analysis") or {}
        prompts = [
            prompt for prompt in prompt_analysis.get("prompts", [])
            if isinstance(prompt, dict) and prompt.get("prompt")
        ][: self.max_questions]

        domain = audit_result.get("domain") or audit_result.get("url") or ""
        brand = (
            prompt_analysis.get("brand")
            or (audit_result.get("positioning_analysis") or {}).get("brand")
            or _brand_from_domain(domain)
        )
        site_url = _normal_site_url(domain)
        official_host = _host(site_url)
        if not prompts:
            return {
                "enabled": True,
                "available": False,
                "reason": "No generated prompts were available for external validation.",
                "providers": [],
                "questions": [],
                "summary": _empty_summary(),
            }

        provider_meta = self._provider_meta()
        available_providers = [
            provider for provider in self.providers
            if provider_meta.get(provider, {}).get("available")
        ]
        if not available_providers:
            return {
                "enabled": True,
                "available": False,
                "reason": "No external AEO provider keys are configured.",
                "providers": [
                    {"name": name, **provider_meta.get(name, {})}
                    for name in self.providers
                ],
                "questions": [],
                "summary": _empty_summary(),
            }

        questions: List[Dict[str, Any]] = []
        for prompt in prompts:
            question = prompt.get("prompt", "")
            provider_results = []
            for provider in available_providers:
                result = self._ask_provider(
                    provider=provider,
                    question=question,
                    brand=brand,
                    site_url=site_url,
                    site_context=site_context or {},
                )
                provider_results.append(result)

            aggregate = self._score_question(prompt, provider_results, brand, official_host)
            questions.append({
                "prompt": question,
                "journey_stage": prompt.get("journey_stage"),
                "journey_label": prompt.get("journey_label"),
                "intent": prompt.get("intent"),
                "internal_eligibility_score": prompt.get(
                    "eligibility_score", prompt.get("answerability_score", 0)
                ),
                "internal_answer_completeness_score": prompt.get(
                    "answer_completeness_score", prompt.get("answerability_score", 0)
                ),
                "providers": provider_results,
                **aggregate,
            })

        summary = self._summarize(questions, available_providers)
        result = {
            "enabled": True,
            "available": True,
            "validated_at": datetime.utcnow().isoformat(),
            "domain": domain,
            "brand": brand,
            "site_url": site_url,
            "providers": [
                {"name": name, **provider_meta.get(name, {})}
                for name in self.providers
            ],
            "summary": summary,
            "questions": questions,
            "artifact_path": "",
        }
        result["artifact_path"] = persist_external_aeo_run(domain, result)
        return result

    def _provider_meta(self) -> Dict[str, Dict[str, Any]]:
        return {
            "openai": {
                "label": "ChatGPT / OpenAI web search",
                "model": self.openai_model,
                "available": bool(os.getenv("OPENAI_API_KEY")) and not _openai_disabled(),
            },
            "gemini": {
                "label": "Gemini with Google Search grounding",
                "model": self.gemini_model,
                "available": bool(os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")),
            },
            "grok": {
                "label": "Grok with xAI web search",
                "model": self.grok_model,
                "available": bool(_xai_api_key()),
            },
        }

    def _ask_provider(
        self,
        provider: str,
        question: str,
        brand: str,
        site_url: str,
        site_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        try:
            if provider == "openai":
                answer, citations = self._ask_openai(question, brand, site_url, site_context)
                model = self.openai_model
            elif provider == "gemini":
                answer, citations = self._ask_gemini(question, brand, site_url, site_context)
                model = self.gemini_model
            elif provider == "grok":
                answer, citations = self._ask_grok(question, brand, site_url, site_context)
                model = self.grok_model
            else:
                raise ValueError(f"Unsupported provider: {provider}")

            scores = _score_answer(answer, citations, brand, _host(site_url))
            return {
                "provider": provider,
                "model": model,
                "available": True,
                "answer": answer,
                "citations": citations[:8],
                **scores,
            }
        except Exception as e:
            logger.warning(f"External AEO provider {provider} failed: {e}")
            return {
                "provider": provider,
                "model": self._provider_meta().get(provider, {}).get("model", ""),
                "available": False,
                "error": str(e),
                "answer": "",
                "citations": [],
                "visibility_score": 0,
                "brand_mentioned": False,
                "official_site_cited": False,
            }

    def _ask_openai(
        self,
        question: str,
        brand: str,
        site_url: str,
        site_context: Dict[str, Any],
    ) -> tuple[str, List[Dict[str, str]]]:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        payload = {
            "model": self.openai_model,
            "tools": [{"type": "web_search_preview"}],
            "input": _provider_prompt(question, brand, site_url, site_context),
        }
        data = _post_json(
            "https://api.openai.com/v1/responses",
            payload,
            {"Authorization": f"Bearer {api_key}"},
            timeout=120,
        )
        answer = data.get("output_text") or _extract_response_text(data)
        citations = _extract_openai_citations(data)
        return answer, citations

    def _ask_gemini(
        self,
        question: str,
        brand: str,
        site_url: str,
        site_context: Dict[str, Any],
    ) -> tuple[str, List[Dict[str, str]]]:
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY or GEMINI_API_KEY is not configured")
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.gemini_model}:generateContent?key={api_key}"
        )
        payload = {
            "contents": [{
                "role": "user",
                "parts": [{"text": _provider_prompt(question, brand, site_url, site_context)}],
            }],
            "tools": [{"google_search": {}}],
            "generationConfig": {"temperature": 0.1},
        }
        data = _post_json(url, payload, {}, timeout=120)
        candidate = (data.get("candidates") or [{}])[0]
        parts = ((candidate.get("content") or {}).get("parts") or [])
        answer = "\n".join(part.get("text", "") for part in parts if part.get("text")).strip()
        citations = _extract_gemini_citations(candidate)
        return answer, citations

    def _ask_grok(
        self,
        question: str,
        brand: str,
        site_url: str,
        site_context: Dict[str, Any],
    ) -> tuple[str, List[Dict[str, str]]]:
        api_key = _xai_api_key()
        if not api_key:
            raise RuntimeError("XAI_API_KEY or GROK_API_KEY is not configured")
        payload = {
            "model": self.grok_model,
            "input": [
                {
                    "role": "user",
                    "content": _provider_prompt(question, brand, site_url, site_context),
                }
            ],
            "tools": [{"type": "web_search"}],
        }
        data = _post_json(
            "https://api.x.ai/v1/responses",
            payload,
            {"Authorization": f"Bearer {api_key}"},
            timeout=180,
        )
        answer = data.get("output_text") or _extract_response_text(data)
        citations = _extract_xai_citations(data)
        return answer, citations

    def _score_question(
        self,
        prompt: Dict[str, Any],
        provider_results: List[Dict[str, Any]],
        brand: str,
        official_host: str,
    ) -> Dict[str, Any]:
        usable = [result for result in provider_results if result.get("available")]
        if not usable:
            return {
                "external_visibility_score": 0,
                "brand_presence_rate": 0,
                "official_citation_rate": 0,
                "internal_external_alignment_score": 0,
            }

        visibility = _avg([result.get("visibility_score", 0) for result in usable])
        brand_rate = round(
            sum(1 for result in usable if result.get("brand_mentioned")) / len(usable) * 100,
            1,
        )
        official_rate = round(
            sum(1 for result in usable if result.get("official_site_cited")) / len(usable) * 100,
            1,
        )
        internal = prompt.get("eligibility_score", prompt.get("answerability_score", 0))
        alignment = max(0, 100 - abs(float(internal or 0) - visibility))
        return {
            "external_visibility_score": round(visibility, 1),
            "brand_presence_rate": brand_rate,
            "official_citation_rate": official_rate,
            "internal_external_alignment_score": round(alignment, 1),
        }

    def _summarize(
        self,
        questions: List[Dict[str, Any]],
        available_providers: List[str],
    ) -> Dict[str, Any]:
        stage_counts: Dict[str, Dict[str, Any]] = {}
        for question in questions:
            stage = question.get("journey_stage") or "unknown"
            bucket = stage_counts.setdefault(
                stage,
                {"total": 0, "external_visibility_score": 0, "brand_presence_rate": 0},
            )
            bucket["total"] += 1
            bucket["external_visibility_score"] += question.get("external_visibility_score", 0)
            bucket["brand_presence_rate"] += question.get("brand_presence_rate", 0)

        for bucket in stage_counts.values():
            total = max(1, bucket["total"])
            bucket["external_visibility_score"] = round(bucket["external_visibility_score"] / total, 1)
            bucket["brand_presence_rate"] = round(bucket["brand_presence_rate"] / total, 1)

        return {
            "questions_tested": len(questions),
            "providers_tested": len(available_providers),
            "external_visibility_score": _avg([
                question.get("external_visibility_score", 0) for question in questions
            ]),
            "brand_presence_rate": _avg([
                question.get("brand_presence_rate", 0) for question in questions
            ]),
            "official_citation_rate": _avg([
                question.get("official_citation_rate", 0) for question in questions
            ]),
            "internal_external_alignment_score": _avg([
                question.get("internal_external_alignment_score", 0) for question in questions
            ]),
            "stage_counts": stage_counts,
        }


def persist_external_aeo_run(domain_url: str, payload: Dict[str, Any]) -> str:
    domain_dir = AEO_RUN_ROOT / _safe_name(_host(domain_url) or _brand_from_domain(domain_url))
    domain_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    path = domain_dir / f"external-aeo-{timestamp}.json"
    latest_path = domain_dir / "latest-external-aeo.json"
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    latest_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return str(path)


def _provider_prompt(
    question: str,
    brand: str,
    site_url: str,
    site_context: Dict[str, Any],
) -> str:
    context_bits = []
    for key in ("business_type", "market_scope", "products", "value_props", "target_audiences"):
        value = site_context.get(key)
        if value:
            context_bits.append(f"{key}: {value}")
    context = "\n".join(context_bits[:6])
    return (
        f"Question: {question}\n\n"
        f"Audited brand: {brand}\n"
        f"Official website: {site_url}\n"
        f"{context}\n\n"
        "Answer the user question as a normal answer engine would. "
        "Do not force the audited brand into the answer if web evidence does not support it."
    )


def _score_answer(
    answer: str,
    citations: List[Dict[str, str]],
    brand: str,
    official_host: str,
) -> Dict[str, Any]:
    answer_l = answer.lower()
    brand_l = brand.lower()
    brand_tokens = [token for token in re.split(r"[^a-z0-9]+", brand_l) if len(token) >= 3]
    brand_mentioned = bool(brand_l and brand_l in answer_l) or any(
        token in answer_l for token in brand_tokens[:2]
    )
    cited_hosts = [_host(item.get("url", "")) for item in citations]
    official_site_cited = bool(official_host and any(
        host == official_host or host.endswith(f".{official_host}")
        for host in cited_hosts
    ))
    answer_quality = min(35, len(answer.split()) * 1.2)
    score = answer_quality
    if brand_mentioned:
        score += 35
    if official_site_cited:
        score += 20
    if citations:
        score += 10
    return {
        "visibility_score": round(max(0, min(100, score)), 1),
        "brand_mentioned": brand_mentioned,
        "official_site_cited": official_site_cited,
        "citation_count": len(citations),
    }


def _post_json(
    url: str,
    payload: Dict[str, Any],
    headers: Dict[str, str],
    timeout: int = 60,
) -> Dict[str, Any]:
    request_headers = {"Content-Type": "application/json", **headers}
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=request_headers,
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            data = json.load(response)
    except HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code}: {body[:300]}")
    return data if isinstance(data, dict) else {}


def _extract_response_text(data: Dict[str, Any]) -> str:
    chunks: List[str] = []
    for item in data.get("output", []):
        for content in item.get("content", []):
            if content.get("text"):
                chunks.append(content["text"])
    return "\n".join(chunks).strip()


def _extract_openai_citations(data: Dict[str, Any]) -> List[Dict[str, str]]:
    citations: List[Dict[str, str]] = []
    for item in data.get("output", []):
        for content in item.get("content", []):
            for annotation in content.get("annotations", []):
                url = annotation.get("url")
                if url:
                    citations.append({"url": url, "title": annotation.get("title", "")})
    return citations


def _extract_xai_citations(data: Dict[str, Any]) -> List[Dict[str, str]]:
    citations: List[Dict[str, str]] = []
    for url in data.get("citations", []) or []:
        if isinstance(url, str):
            citations.append({"url": url, "title": ""})
    citations.extend(_extract_openai_citations(data))
    seen = set()
    unique = []
    for citation in citations:
        url = citation.get("url")
        if url and url not in seen:
            seen.add(url)
            unique.append(citation)
    return unique


def _extract_gemini_citations(candidate: Dict[str, Any]) -> List[Dict[str, str]]:
    metadata = candidate.get("groundingMetadata") or {}
    citations: List[Dict[str, str]] = []
    for chunk in metadata.get("groundingChunks", []):
        web = chunk.get("web") or {}
        uri = web.get("uri")
        if uri:
            citations.append({"url": uri, "title": web.get("title", "")})
    return citations


def _normal_site_url(value: str) -> str:
    if not value:
        return ""
    return value if "://" in value else f"https://{value}"


def _host(value: str) -> str:
    parsed = urlparse(value if "://" in value else f"https://{value}")
    return (parsed.netloc or parsed.path.split("/")[0]).replace("www.", "").lower()


def _brand_from_domain(value: str) -> str:
    host = _host(value)
    if not host:
        return "this brand"
    return host.split(".")[0].replace("-", " ").title()


def _safe_name(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip("-._")
    return cleaned or "site"


def _env_list(name: str) -> List[str]:
    raw = os.getenv(name, "")
    return [item.strip().lower() for item in raw.split(",") if item.strip()]


def _xai_api_key() -> str:
    return os.getenv("XAI_API_KEY") or os.getenv("GROK_API_KEY") or ""


def _avg(values: List[float | int]) -> float:
    if not values:
        return 0.0
    return round(sum(float(value or 0) for value in values) / len(values), 1)


def _empty_summary() -> Dict[str, Any]:
    return {
        "questions_tested": 0,
        "providers_tested": 0,
        "external_visibility_score": 0,
        "brand_presence_rate": 0,
        "official_citation_rate": 0,
        "internal_external_alignment_score": 0,
        "stage_counts": {},
    }
