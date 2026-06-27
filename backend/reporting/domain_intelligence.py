"""
Domain intelligence preflight for targeted crawling and demand questions.
"""
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

try:
    from config import settings
except Exception:
    import os

    class _FallbackSettings:
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        DOMAIN_INTELLIGENCE_MODEL = os.getenv("DOMAIN_INTELLIGENCE_MODEL", "gpt-4o-mini")

    settings = _FallbackSettings()


REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = Path(os.getenv("AEO_DATA_DIR", REPO_ROOT / "domains")).expanduser()
INTELLIGENCE_ROOT = DATA_ROOT / "intelligence"


DOMAIN_INTELLIGENCE_PROMPT = """
You are a domain intelligence analyst for an Answer Engine Optimization audit.

Given the domain and any website evidence below, produce a compact,
evidence-aware analysis of the business, website structure, competitors, and
likely user questions.

Domain:
{domain}

Website evidence:
{website_evidence}

Important constraints:
- Do not invent specifics that are not commonly knowable from the domain, brand, or public context.
- Treat supplied website evidence as authoritative. Infer from the domain alone only when evidence is absent.
- If uncertain, mark fields as "unknown" and explain what the crawler should verify.
- Prefer practical audit guidance over marketing language.
- Competitors should include direct competitors, adjacent alternatives, and category comparators where relevant.
- User questions should reflect what real users ask before trusting, comparing, or choosing this type of website/service.
- First identify the commercial model. Do not ask product-pricing questions about consultancies, education providers, managed services, or other quote-led businesses unless the evidence makes pricing a genuine buyer concern.
- Prefer questions about buyer risks, evaluation method, fit, outcomes, proof, differentiation, and engagement process over generic brand questions.
- Return only valid JSON. No markdown.

JSON schema:
{{
  "domain": "string",
  "brand_guess": "string",
  "confidence": "high|medium|low",
  "business": {{
    "entity_type": "string",
    "category": "string",
    "one_line_description": "string",
    "primary_audience": ["string"],
    "core_offers": ["string"],
    "likely_revenue_model": ["string"],
    "market_scope": "local|regional|national|global|unknown",
    "locations_or_markets": ["string"],
    "things_to_verify": ["string"]
  }},
  "website_structure_hypothesis": {{
    "likely_important_sections": [
      {{
        "section": "string",
        "why_it_matters": "string",
        "crawler_priority": "high|medium|low",
        "url_patterns_to_look_for": ["string"]
      }}
    ],
    "pages_to_deprioritize": [
      {{
        "section": "string",
        "reason": "string",
        "url_patterns": ["string"]
      }}
    ],
    "crawl_strategy": {{
      "start_pages": ["string"],
      "must_include_patterns": ["string"],
      "avoid_patterns": ["string"],
      "max_depth_guidance": "string"
    }}
  }},
  "competitive_landscape": {{
    "direct_competitors": [
      {{
        "name": "string",
        "domain": "string|unknown",
        "why_relevant": "string",
        "confidence": "high|medium|low"
      }}
    ],
    "adjacent_alternatives": [
      {{
        "name": "string",
        "category": "string",
        "why_users_compare_it": "string"
      }}
    ],
    "category_expectations": ["string"]
  }},
  "question_strategy": {{
    "problem_aware_questions": ["string"],
    "solution_aware_questions": ["string"],
    "comparison_questions": ["string"],
    "trust_questions": ["string"],
    "conversion_questions": ["string"],
    "support_or_post_purchase_questions": ["string"],
    "questions_to_avoid": ["string"]
  }},
  "crawler_verification_tasks": [
    {{
      "task": "string",
      "why": "string",
      "evidence_to_extract": ["string"]
    }}
  ]
}}
"""

FINAL_STRATEGY_PROMPT = """
You are the final strategy analyst for an Answer Engine Optimization audit.

Use the crawled website evidence as the primary source of truth. Review the
preliminary domain hypothesis, correct it where the evidence disagrees, and
produce the final business context and realistic buyer-question strategy.

Domain:
{domain}

Preliminary hypothesis:
{preliminary_intelligence}

Crawled website evidence:
{website_evidence}

Requirements:
- Identify the commercial model before writing any questions.
- First extract the problems solved, buyer jobs, solution categories, use cases,
  desired outcomes, alternatives, and evidence needed to recommend the company.
- Questions must sound like questions a real buyer, evaluator, learner, or
  stakeholder would ask while deciding whether the organization can help them.
- Most questions must be unbranded. They should describe the user's problem or
  desired outcome so the audited company could be inferred as a relevant answer.
- Prefer risk, method, fit, outcome, proof, differentiation, implementation,
  and engagement questions.
- Do not ask about standardized price, subscriptions, buying the brand, or
  product features unless the evidence shows those concepts genuinely apply.
- Reject generic questions that could be asked unchanged about nearly any company.
- Use concise natural language and return only valid JSON.

Return the same top-level schema as the preliminary response, but use this
question_strategy structure:
{{
  "problem_recognition_questions": ["3-5 unbranded questions about the underlying problem"],
  "solution_discovery_questions": ["3-5 unbranded questions seeking a category or provider"],
  "use_case_fit_questions": ["3-5 unbranded questions about concrete use cases and outcomes"],
  "provider_comparison_questions": ["2-4 mostly unbranded comparison questions"],
  "branded_validation_questions": ["2-4 questions that explicitly name the audited brand"],
  "implementation_questions": ["1-3 onboarding, integration, support, security, or procurement questions"],
  "questions_to_avoid": ["unsupported or commercially irrelevant question patterns"]
}}

Order questions inside each group from highest to lowest buyer importance.
"""


class DomainIntelligencePreflight:
    """Build and persist a pre-crawl hypothesis for a domain."""

    def __init__(self, model: str | None = None):
        selected_model = model or getattr(
            settings, "DOMAIN_INTELLIGENCE_MODEL", "gpt-4o-mini"
        )
        self.llm = JSONLLMClient(
            selected_model,
            getattr(settings, "DOMAIN_INTELLIGENCE_MODEL", "gpt-4o-mini"),
            os.getenv("OLLAMA_DOMAIN_MODEL", "gpt-oss:20b"),
        )
        self.model = self.llm.model
        self.provider = self.llm.provider
        self.available = self.llm.available

    def analyze(self, domain_url: str, options: Dict[str, Any] | None = None) -> Dict[str, Any]:
        options = options or {}
        if options.get("skip_domain_intelligence"):
            return self._fallback(domain_url, "Domain intelligence skipped by options.")

        if options.get("use_cached_domain_intelligence"):
            cached = load_domain_intelligence(domain_url)
            if cached:
                return cached

        if not self.available:
            intelligence = self._fallback(
                domain_url, f"{self.provider} model provider is not available."
            )
            persist_domain_intelligence(domain_url, intelligence)
            return intelligence

        try:
            intelligence = self._call_model(
                domain_url, options.get("domain_evidence") or ""
            )
        except Exception as e:
            logger.warning(f"Domain intelligence failed for {domain_url}: {e}")
            intelligence = self._fallback(domain_url, str(e))

        persist_domain_intelligence(domain_url, intelligence)
        return intelligence

    def _call_model(self, domain_url: str, website_evidence: str = "") -> Dict[str, Any]:
        payload = self.llm.generate_json(
            "Return only valid JSON for a domain intelligence preflight.",
            DOMAIN_INTELLIGENCE_PROMPT.format(
                domain=domain_url,
                website_evidence=website_evidence or "No website evidence supplied.",
            ),
            temperature=0.2,
        )
        payload["_source"] = self.provider
        payload["_provider"] = self.provider
        payload["_model"] = self.model
        payload["_generated_at"] = datetime.utcnow().isoformat()
        return normalize_domain_intelligence(domain_url, payload)

    def _fallback(self, domain_url: str, reason: str) -> Dict[str, Any]:
        domain = _domain_key(domain_url)
        brand = domain.split(".")[0].replace("-", " ").replace("_", " ").title()
        payload = {
            "domain": domain_url,
            "brand_guess": brand,
            "confidence": "low",
            "business": {
                "entity_type": "unknown",
                "category": "unknown",
                "one_line_description": "unknown",
                "primary_audience": [],
                "core_offers": [],
                "likely_revenue_model": [],
                "market_scope": "unknown",
                "locations_or_markets": [],
                "things_to_verify": [
                    "Business type, audience, offers, proof points, pricing, competitors, and conversion paths."
                ],
            },
            "website_structure_hypothesis": {
                "likely_important_sections": [
                    {
                        "section": "homepage",
                        "why_it_matters": "Primary positioning and navigation entry point.",
                        "crawler_priority": "high",
                        "url_patterns_to_look_for": ["/"],
                    },
                    {
                        "section": "about",
                        "why_it_matters": "Explains audience, business identity, team, and credibility.",
                        "crawler_priority": "high",
                        "url_patterns_to_look_for": ["/about"],
                    },
                    {
                        "section": "products or services",
                        "why_it_matters": "Explains what users can buy, use, join, or request.",
                        "crawler_priority": "high",
                        "url_patterns_to_look_for": ["/product", "/service", "/solution", "/offering"],
                    },
                    {
                        "section": "pricing or contact",
                        "why_it_matters": "Helps answer conversion and commercial-intent questions.",
                        "crawler_priority": "medium",
                        "url_patterns_to_look_for": ["/pricing", "/contact", "/book", "/demo"],
                    },
                ],
                "pages_to_deprioritize": [
                    {
                        "section": "legal",
                        "reason": "Rarely useful for user demand questions.",
                        "url_patterns": ["/privacy", "/terms", "/cookie"],
                    }
                ],
                "crawl_strategy": {
                    "start_pages": ["/"],
                    "must_include_patterns": [
                        "/about", "/product", "/service", "/solution", "/pricing", "/contact", "/faq"
                    ],
                    "avoid_patterns": ["/privacy", "/terms", "/cookie"],
                    "max_depth_guidance": "Prioritize high-intent business, offer, proof, and conversion pages.",
                },
            },
            "competitive_landscape": {
                "direct_competitors": [],
                "adjacent_alternatives": [],
                "category_expectations": [],
            },
            "question_strategy": {
                "problem_aware_questions": [],
                "solution_aware_questions": [],
                "comparison_questions": [],
                "trust_questions": [
                    f"What is {brand}?",
                    f"Who is {brand} for?",
                    f"Is {brand} trustworthy?",
                ],
                "conversion_questions": [
                    f"How do I get started with {brand}?",
                ],
                "support_or_post_purchase_questions": [],
                "questions_to_avoid": [
                    "marketing slogans as questions",
                    "privacy policy questions",
                    "incomplete page heading fragments",
                ],
            },
            "crawler_verification_tasks": [
                {
                    "task": "Verify business identity and primary offer.",
                    "why": "The preflight could not use external intelligence.",
                    "evidence_to_extract": ["homepage hero", "about page", "services/products pages"],
                }
            ],
            "_source": "fallback",
            "_reason": reason,
            "_generated_at": datetime.utcnow().isoformat(),
        }
        return normalize_domain_intelligence(domain_url, payload)


class DomainStrategySynthesizer:
    """Build the final evidence-backed business and question strategy once."""

    def __init__(self, model: str | None = None):
        selected_model = model or "auto"
        self.llm = JSONLLMClient(
            selected_model,
            getattr(settings, "DOMAIN_INTELLIGENCE_MODEL", "gpt-4o-mini"),
            os.getenv("OLLAMA_STRATEGY_MODEL", "qwen3.5:397b"),
        )
        self.model = self.llm.model
        self.provider = self.llm.provider

    def analyze(
        self,
        domain_url: str,
        website_evidence: str,
        preliminary_intelligence: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        if not self.llm.available or not website_evidence.strip():
            return preliminary_intelligence or {}

        payload = self.llm.generate_json(
            "Return only valid JSON for the final evidence-backed domain strategy.",
            FINAL_STRATEGY_PROMPT.format(
                domain=domain_url,
                preliminary_intelligence=json.dumps(
                    preliminary_intelligence or {},
                    indent=2,
                    default=str,
                )[:12000],
                website_evidence=website_evidence,
            ),
            temperature=0.2,
        )
        payload["_source"] = self.provider
        payload["_provider"] = self.provider
        payload["_model"] = self.model
        payload["_stage"] = "final_strategy"
        payload["_generated_at"] = datetime.utcnow().isoformat()
        normalized = normalize_domain_intelligence(domain_url, payload)
        persist_domain_strategy(domain_url, normalized)
        return normalized


def normalize_domain_intelligence(domain_url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    payload["domain"] = str(payload.get("domain") or domain_url)
    payload["brand_guess"] = str(payload.get("brand_guess") or _domain_key(domain_url).split(".")[0])
    if payload.get("confidence") not in {"high", "medium", "low"}:
        payload["confidence"] = "low"

    payload["business"] = payload.get("business") if isinstance(payload.get("business"), dict) else {}
    payload["website_structure_hypothesis"] = (
        payload.get("website_structure_hypothesis")
        if isinstance(payload.get("website_structure_hypothesis"), dict)
        else {}
    )
    payload["competitive_landscape"] = (
        payload.get("competitive_landscape")
        if isinstance(payload.get("competitive_landscape"), dict)
        else {}
    )
    payload["question_strategy"] = (
        payload.get("question_strategy")
        if isinstance(payload.get("question_strategy"), dict)
        else {}
    )
    tasks = payload.get("crawler_verification_tasks")
    payload["crawler_verification_tasks"] = tasks if isinstance(tasks, list) else []
    payload["_quality_warnings"] = _quality_warnings(payload)
    return payload


def merge_intelligence_into_site_context(
    site_context: Dict[str, Any],
    intelligence: Dict[str, Any],
) -> Dict[str, Any]:
    """Use preflight as weak defaults while preserving explicit site context."""
    merged = dict(site_context or {})
    business = intelligence.get("business") or {}

    defaults = {
        "brand": intelligence.get("brand_guess"),
        "entity_type": business.get("entity_type"),
        "business_type": business.get("category"),
        "market_scope": business.get("market_scope"),
        "locations": business.get("locations_or_markets"),
        "offers": business.get("core_offers"),
        "audience": business.get("primary_audience"),
    }

    for key, value in defaults.items():
        if key not in merged and _usable_context_value(value):
            merged[key] = value
    if (
        "question_strategy" not in merged
        and _has_actionable_question_strategy(intelligence.get("question_strategy"))
    ):
        merged["question_strategy"] = intelligence.get("question_strategy")
    if "_context_path" not in merged:
        merged["_context_path"] = intelligence.get("_artifact_path") or "domain_intelligence"
    return merged


def _usable_context_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip()) and value.strip().lower() not in {"unknown", "n/a", "none"}
    if isinstance(value, list):
        return any(_usable_context_value(item) for item in value)
    if isinstance(value, dict):
        return any(_usable_context_value(item) for item in value.values())
    return bool(value)


def _has_actionable_question_strategy(strategy: Any) -> bool:
    if not isinstance(strategy, dict):
        return False
    new_demand_buckets = [
        "problem_recognition_questions",
        "solution_discovery_questions",
        "use_case_fit_questions",
        "provider_comparison_questions",
        "branded_validation_questions",
        "implementation_questions",
    ]
    legacy_demand_buckets = [
        "problem_aware_questions",
        "solution_aware_questions",
        "comparison_questions",
        "trust_questions",
        "conversion_questions",
        "support_or_post_purchase_questions",
    ]
    demand_buckets = (
        new_demand_buckets
        if any(strategy.get(bucket) for bucket in new_demand_buckets)
        else legacy_demand_buckets
    )
    non_empty_buckets = 0
    total_questions = 0
    for bucket in demand_buckets:
        questions = []
        for item in strategy.get(bucket, []):
            if isinstance(item, str) and item.strip():
                questions.append(item)
            elif isinstance(item, dict):
                question = item.get("question") or item.get("prompt")
                if isinstance(question, str) and question.strip():
                    questions.append(question)
        if questions:
            non_empty_buckets += 1
            total_questions += len(questions)
    category_buckets = (
        [
            "problem_recognition_questions",
            "solution_discovery_questions",
            "use_case_fit_questions",
        ]
        if demand_buckets == new_demand_buckets
        else [
            "problem_aware_questions",
            "solution_aware_questions",
            "comparison_questions",
        ]
    )
    has_category_depth = any(
        isinstance(strategy.get(bucket), list) and strategy.get(bucket)
        for bucket in category_buckets
    )
    return total_questions >= 6 and non_empty_buckets >= 3 and has_category_depth


def _quality_warnings(payload: Dict[str, Any]) -> List[str]:
    warnings: List[str] = []
    business = payload.get("business") if isinstance(payload.get("business"), dict) else {}
    if payload.get("confidence") == "low":
        warnings.append("domain intelligence confidence is low")
    if not _usable_context_value(business.get("category")):
        warnings.append("business category is unknown")
    if not _usable_context_value(business.get("core_offers")):
        warnings.append("core offers are missing")
    if not _has_actionable_question_strategy(payload.get("question_strategy")):
        warnings.append("question strategy is too sparse for prompt generation")
    return warnings


def prioritize_urls_with_intelligence(
    urls: List[str],
    intelligence: Dict[str, Any],
    max_pages: int,
) -> List[str]:
    """Sort URLs so crawler spends budget on pages preflight says matter."""
    strategy = (intelligence.get("website_structure_hypothesis") or {}).get("crawl_strategy") or {}
    sections = (intelligence.get("website_structure_hypothesis") or {}).get("likely_important_sections") or []
    must_patterns = _patterns(strategy.get("must_include_patterns"))
    avoid_patterns = _patterns(strategy.get("avoid_patterns"))
    start_pages = _patterns(strategy.get("start_pages"))
    high_patterns: List[str] = []

    for section in sections:
        if not isinstance(section, dict):
            continue
        if section.get("crawler_priority") == "high":
            high_patterns.extend(_patterns(section.get("url_patterns_to_look_for")))

    def score(url: str) -> int:
        url_l = url.lower()
        value = 0
        if any(_pattern_matches(url_l, pattern) for pattern in start_pages):
            value += 40
        if any(_pattern_matches(url_l, pattern) for pattern in must_patterns):
            value += 30
        if any(_pattern_matches(url_l, pattern) for pattern in high_patterns):
            value += 20
        if any(_pattern_matches(url_l, pattern) for pattern in avoid_patterns):
            value -= 50
        if re.search(r"/(privacy|terms|cookie|login|signup|cart|checkout)", url_l):
            value -= 20
        if urlparse(url).path in {"", "/"}:
            value += 50
        return value

    ordered = sorted(dict.fromkeys(urls), key=lambda item: (-score(item), len(item), item))
    if max_pages > 0 and max_pages < 9999:
        return ordered[:max_pages]
    return ordered


def load_domain_intelligence(domain_url: str) -> Dict[str, Any]:
    path = _intelligence_path(domain_url)
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning(f"Failed to load domain intelligence {path}: {e}")
        return {}
    if not isinstance(payload, dict):
        return {}
    payload = normalize_domain_intelligence(domain_url, payload)
    payload["_artifact_path"] = str(path)
    return payload


def persist_domain_intelligence(domain_url: str, payload: Dict[str, Any]) -> str:
    path = _intelligence_path(domain_url)
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = normalize_domain_intelligence(domain_url, payload)
    normalized["_artifact_path"] = str(path)
    path.write_text(json.dumps(normalized, indent=2, default=str), encoding="utf-8")
    logger.info(f"Persisted domain intelligence for {domain_url} to {path}")
    return str(path)


def persist_domain_strategy(domain_url: str, payload: Dict[str, Any]) -> str:
    path = INTELLIGENCE_ROOT / f"{_domain_key(domain_url)}.strategy.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = normalize_domain_intelligence(domain_url, payload)
    normalized["_artifact_path"] = str(path)
    path.write_text(json.dumps(normalized, indent=2, default=str), encoding="utf-8")
    logger.info(f"Persisted final domain strategy for {domain_url} to {path}")
    return str(path)


def _intelligence_path(domain_url: str) -> Path:
    return INTELLIGENCE_ROOT / f"{_domain_key(domain_url)}.json"


def _domain_key(domain_url: str) -> str:
    parsed = urlparse(domain_url if "://" in domain_url else f"https://{domain_url}")
    host = parsed.netloc or parsed.path.split("/")[0] or "site"
    host = host.replace("www.", "")
    return re.sub(r"[^a-zA-Z0-9._-]+", "-", host).strip("-._") or "site"


def _patterns(value: Any) -> List[str]:
    if isinstance(value, str):
        return [value.lower()]
    if isinstance(value, list):
        return [str(item).lower() for item in value if str(item).strip()]
    return []


def _pattern_matches(url_l: str, pattern: str) -> bool:
    if not pattern:
        return False
    if pattern == "/":
        return urlparse(url_l).path in {"", "/"}
    return pattern.strip("*") in url_l
