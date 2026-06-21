"""
LLM-based prompt answerability judge.

This module independently evaluates whether retrieved local evidence can answer
each prompt. It is intentionally constrained to the supplied evidence only.
"""
import json
import logging
import os
from typing import Any, Dict, List

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
        self.model = model or settings.PROMPT_EVAL_MODEL
        self.available = bool(settings.OPENAI_API_KEY)
        self.client = None

        if not self.available:
            return

        try:
            from openai import OpenAI

            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        except Exception as e:
            logger.warning(f"LLM prompt evaluator unavailable: {e}")
            self.available = False

    def evaluate_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not self.available or not self.client:
            return {
                "enabled": False,
                "provider": "openai",
                "model": self.model,
                "reason": "OPENAI_API_KEY or OpenAI client is not available",
                "results": results,
            }

        evaluated: List[Dict[str, Any]] = []
        max_prompts = max(1, settings.PROMPT_EVAL_MAX_PROMPTS)

        for i, result in enumerate(results):
            if i >= max_prompts:
                evaluated.append(result)
                continue
            evaluated.append(self.evaluate_prompt(result))

        return {
            "enabled": True,
            "provider": "openai",
            "model": self.model,
            "evaluated_prompts": min(len(results), max_prompts),
            "results": evaluated,
        }

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

        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a strict answerability evaluator for website audits. "
                        "Return only JSON. If the evidence is vague, generic, or does "
                        "not directly answer the prompt, lower the coverage."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        user_prompt
                        + "\nReturn JSON with keys: coverage "
                        "(strong|partial|weak|missing), answerability_score (0-100), "
                        "answer (string), reasoning (string), gaps (array of strings), "
                        "recommended_fix (string), evidence_used (array of evidence numbers)."
                    ),
                },
            ],
        )

        content = response.choices[0].message.content or "{}"
        return json.loads(content)

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
        if evaluation.get("reasoning"):
            result["gap"] = evaluation["reasoning"]
        if evaluation.get("recommended_fix"):
            result["recommended_fix"] = evaluation["recommended_fix"]
        return result
