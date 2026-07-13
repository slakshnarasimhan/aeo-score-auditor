"""
LLM-based prompt answerability judge.

This module independently evaluates whether retrieved local evidence can answer
each prompt. It is intentionally constrained to the supplied evidence only.
"""
import json
import logging
import os
from typing import Any, Dict, List

from reporting.llm_client import JSONLLMClient

try:
    from loguru import logger
except Exception:
    logger = logging.getLogger(__name__)

try:
    from config import settings
except Exception:
    class _FallbackSettings:
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        PROMPT_EVAL_MODEL = os.getenv("PROMPT_EVAL_MODEL", "gpt-4o-mini")
        PROMPT_EVAL_MAX_PROMPTS = int(os.getenv("PROMPT_EVAL_MAX_PROMPTS", "12"))

    settings = _FallbackSettings()


class LLMPromptEvaluator:
    """Use an LLM to judge prompt coverage from local site evidence."""

    def __init__(self, model: str | None = None):
        selected_model = model or settings.PROMPT_EVAL_MODEL
        self.llm = JSONLLMClient(
            selected_model,
            settings.PROMPT_EVAL_MODEL,
            os.getenv("OLLAMA_DOMAIN_MODEL", "gpt-oss:20b"),
        )
        self.model = self.llm.model
        self.provider = self.llm.provider
        self.available = self.llm.available

    def evaluate_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not self.available:
            return {
                "enabled": False,
                "provider": self.provider,
                "model": self.model,
                "reason": f"{self.provider} model provider is not available",
                "results": results,
            }

        max_prompts = max(1, settings.PROMPT_EVAL_MAX_PROMPTS)
        evaluated = list(results)
        batch_indexes = [
            index for index, result in enumerate(results[:max_prompts])
            if result.get("evidence")
        ]
        for index, result in enumerate(results[:max_prompts]):
            if not result.get("evidence"):
                result["llm_evaluation"] = self._missing_eval(
                    "No local evidence was retrieved."
                )
                evaluated[index] = self._apply_llm_eval(result)

        if batch_indexes:
            try:
                payload = self._call_batch([
                    results[index] for index in batch_indexes
                ])
                response_items = payload.get("evaluations", [])
                by_id = {
                    int(item.get("id")): item
                    for item in response_items
                    if isinstance(item, dict) and str(item.get("id", "")).isdigit()
                }
                for batch_id, result_index in enumerate(batch_indexes):
                    result = results[result_index]
                    item = by_id.get(batch_id)
                    if item:
                        result["llm_evaluation"] = self._normalize_eval(item)
                        evaluated[result_index] = self._apply_llm_eval(result)
            except Exception as e:
                logger.warning(f"Batched LLM prompt evaluation failed: {e}")

        return {
            "enabled": True,
            "provider": self.provider,
            "model": self.model,
            "evaluated_prompts": min(len(results), max_prompts),
            "results": evaluated,
        }

    def _call_batch(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        items = []
        for index, result in enumerate(results):
            evidence = [
                {
                    "number": evidence_index + 1,
                    "url": item.get("url", ""),
                    "type": item.get("type", ""),
                    "text": item.get("text", ""),
                }
                for evidence_index, item in enumerate(result.get("evidence", [])[:5])
            ]
            items.append({
                "id": index,
                "prompt": result.get("prompt", ""),
                "intent": result.get("intent", ""),
                "evidence": evidence,
            })

        return self.llm.generate_json(
            (
                "You are an evidence-grounded answerability evaluator. Evaluate every "
                "item independently using only its supplied website evidence. First "
                "synthesize the best direct answer the evidence supports, then judge "
                "coverage. Evidence may be spread across multiple snippets; do not "
                "downgrade solely because the answer is assembled from several snippets. "
                "Use partial or weak only when important answer details are absent, "
                "ambiguous, or contradicted."
            ),
            (
                f"Items:\n{json.dumps(items, default=str)}\n\n"
                "Return JSON with an evaluations array. Each evaluation must contain "
                "id, coverage (strong|partial|weak|missing), answerability_score "
                "(0-100), answer, reasoning, gaps, recommended_fix, and evidence_used. "
                "The answer must cite only facts present in the supplied evidence. If "
                "the evidence supports a qualified answer, state the qualification."
            ),
            temperature=0,
        )

    def evaluate_prompt(self, result: Dict[str, Any]) -> Dict[str, Any]:
        evidence = result.get("evidence", [])
        if not evidence:
            result["llm_evaluation"] = self._missing_eval("No local evidence was retrieved.")
            return self._apply_llm_eval(result)

        try:
            payload = self._call_llm(result)
            result["llm_evaluation"] = self._normalize_eval(payload)
        except Exception as e:
            logger.warning(f"LLM prompt evaluation failed for '{result.get('prompt')}': {e}")
            result["llm_evaluation"] = {
                "available": False,
                "error": str(e),
            }
            return result

        return self._apply_llm_eval(result)

    def _call_llm(self, result: Dict[str, Any]) -> Dict[str, Any]:
        evidence_text = "\n\n".join(
            f"[{i + 1}] URL: {item.get('url', '')}\n"
            f"Type: {item.get('type', '')}\n"
            f"Evidence: {item.get('text', '')}"
            for i, item in enumerate(result.get("evidence", [])[:5])
        )

        user_prompt = f"""
User prompt:
{result.get('prompt', '')}

Intent:
{result.get('intent', '')}

Retrieved local website evidence:
{evidence_text}

Judge whether the evidence from this website can answer the user prompt.
Use only the evidence above. Do not use outside knowledge.
"""

        return self.llm.generate_json(
            (
                "You are an evidence-grounded answerability evaluator for website audits. "
                "Return only JSON. First synthesize the best direct answer supported by "
                "the retrieved evidence, then judge coverage. Evidence may be spread "
                "across multiple snippets; do not downgrade solely because the answer "
                "requires combining snippets. If the evidence is vague, generic, "
                "ambiguous, contradicted, or missing important details, lower the coverage."
            ),
            (
                user_prompt
                + "\nReturn JSON with keys: coverage "
                "(strong|partial|weak|missing), answerability_score (0-100), "
                "answer (string), reasoning (string), gaps (array of strings), "
                "recommended_fix (string), evidence_used (array of evidence numbers). "
                "Use only facts in the evidence. If the evidence supports a qualified "
                "answer, state the qualification."
            ),
            temperature=0,
        )

    def _normalize_eval(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        coverage = str(payload.get("coverage", "missing")).lower()
        if coverage not in {"strong", "partial", "weak", "missing"}:
            coverage = "missing"

        try:
            score = int(payload.get("answerability_score", 0))
        except (TypeError, ValueError):
            score = 0

        gaps = payload.get("gaps", [])
        if not isinstance(gaps, list):
            gaps = [str(gaps)]

        evidence_used = payload.get("evidence_used", [])
        if not isinstance(evidence_used, list):
            evidence_used = []

        return {
            "available": True,
            "coverage": coverage,
            "answerability_score": max(0, min(100, score)),
            "answer": str(payload.get("answer", "")),
            "reasoning": str(payload.get("reasoning", "")),
            "gaps": [str(gap) for gap in gaps[:5]],
            "recommended_fix": str(payload.get("recommended_fix", "")),
            "evidence_used": evidence_used[:5],
        }

    def _missing_eval(self, reason: str) -> Dict[str, Any]:
        return {
            "available": True,
            "coverage": "missing",
            "answerability_score": 0,
            "answer": "",
            "reasoning": reason,
            "gaps": [reason],
            "recommended_fix": "Add a direct FAQ or page section that answers this prompt.",
            "evidence_used": [],
        }

    def _apply_llm_eval(self, result: Dict[str, Any]) -> Dict[str, Any]:
        evaluation = result.get("llm_evaluation") or {}
        if not evaluation.get("available"):
            return result

        result["deterministic_coverage"] = result.get("coverage")
        result["deterministic_answerability_score"] = result.get("answerability_score")
        result["coverage"] = evaluation.get("coverage", result.get("coverage"))
        result["answerability_score"] = evaluation.get(
            "answerability_score", result.get("answerability_score")
        )
        if evaluation.get("answer"):
            result["answer"] = evaluation["answer"]
        if evaluation.get("reasoning"):
            result["gap"] = evaluation["reasoning"]
        if evaluation.get("recommended_fix"):
            result["recommended_fix"] = evaluation["recommended_fix"]
        return result
