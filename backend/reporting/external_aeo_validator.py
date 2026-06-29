"""External answer-engine validation for generated AEO questions."""
from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlparse

from reporting.llm_client import JSONLLMClient

try:
    from loguru import logger
except Exception:
    import logging

    logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = Path(os.getenv("AEO_DATA_DIR", REPO_ROOT / "domains")).expanduser()
AEO_RUN_ROOT = DATA_ROOT / "aeo_runs"


class ExternalAEOValidator:
    """Ask generated questions to external answer engines and score visibility."""

    PROVIDERS = ("ollama",)

    def __init__(self, providers: List[str] | None = None, max_questions: int | None = None):
        self.providers = ["ollama"]
        self.max_questions = max_questions or int(os.getenv("EXTERNAL_AEO_MAX_QUESTIONS", "12"))
        self.ollama_model = os.getenv(
            "EXTERNAL_AEO_OLLAMA_MODEL",
            os.getenv("PROMPT_EVAL_MODEL", "ollama:glm-5.2"),
        )
        self.ollama_client = JSONLLMClient(
            self.ollama_model,
            "gpt-4o-mini",
            os.getenv("OLLAMA_VALIDATOR_MODEL", "glm-5.2"),
        )

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
            "ollama": {
                "label": "Ollama answer-engine simulation",
                "model": self.ollama_client.model,
                "available": self.ollama_client.available,
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
            if provider != "ollama":
                raise ValueError(f"Unsupported provider: {provider}")
            answer, citations = self._ask_ollama(question, brand, site_url, site_context)
            model = self.ollama_client.model

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

    def _ask_ollama(
        self,
        question: str,
        brand: str,
        site_url: str,
        site_context: Dict[str, Any],
    ) -> tuple[str, List[Dict[str, str]]]:
        if not self.ollama_client.available:
            raise RuntimeError("Ollama model provider is not available")

        payload = self.ollama_client.generate_json(
            (
                "You simulate an answer engine for AEO validation. Return only JSON. "
                "Answer naturally from the supplied question and context. Do not invent "
                "web citations."
            ),
            (
                _provider_prompt(question, brand, site_url, site_context)
                + "\n\nReturn JSON with keys: answer (string), citations "
                "(array of objects with url and title; use [] unless the official website "
                "is directly relevant and named in your answer)."
            ),
            temperature=0.1,
        )
        answer = str(payload.get("answer", "")).strip()
        citations = payload.get("citations", [])
        if not isinstance(citations, list):
            citations = []
        normalized = [
            {
                "url": str(item.get("url", "")).strip(),
                "title": str(item.get("title", "")).strip(),
            }
            for item in citations
            if isinstance(item, dict) and item.get("url")
        ]
        return answer, normalized

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
