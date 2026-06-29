import unittest
from unittest.mock import patch

from reporting.llm_client import _parse_json_object, parse_model_spec
from reporting.external_aeo_validator import ExternalAEOValidator
from reporting.llm_prompt_evaluator import LLMPromptEvaluator


class _FakeLLM:
    def __init__(self):
        self.calls = 0

    def generate_json(self, system_prompt, user_prompt, temperature=0):
        self.calls += 1
        return {
            "evaluations": [
                {
                    "id": 0,
                    "coverage": "strong",
                    "answerability_score": 90,
                    "answer": "Answered",
                    "reasoning": "Direct evidence",
                    "gaps": [],
                    "recommended_fix": "",
                    "evidence_used": [1],
                },
                {
                    "id": 1,
                    "coverage": "partial",
                    "answerability_score": 55,
                    "answer": "Partially answered",
                    "reasoning": "Some detail is missing",
                    "gaps": ["Method detail"],
                    "recommended_fix": "Explain the method.",
                    "evidence_used": [1],
                },
            ]
        }


class ModelRoutingTests(unittest.TestCase):
    def test_explicit_ollama_model_keeps_provider_and_name(self):
        self.assertEqual(
            parse_model_spec("ollama:gpt-oss:20b", "gpt-4o-mini"),
            ("ollama", "gpt-oss:20b"),
        )

    def test_disable_openai_marks_auto_provider_disabled_without_ollama(self):
        with patch.dict("os.environ", {"DISABLE_OPENAI": "true"}, clear=True):
            self.assertEqual(
                parse_model_spec("auto", "gpt-4o-mini"),
                ("disabled", "gpt-4o-mini"),
            )

    def test_external_aeo_validation_is_ollama_only(self):
        with patch.dict("os.environ", {"OLLAMA_KEY": "test"}, clear=True):
            validator = ExternalAEOValidator(providers=["openai", "gemini"])
            self.assertEqual(validator.providers, ["ollama"])

    def test_json_parser_extracts_object_from_model_wrapper(self):
        self.assertEqual(
            _parse_json_object('```json\\n{"answer": "ok"}\\n```'),
            {"answer": "ok"},
        )
        self.assertEqual(
            _parse_json_object('</think> {"answer": "ok"} extra text'),
            {"answer": "ok"},
        )

    def test_answerability_results_are_evaluated_in_one_batch(self):
        evaluator = LLMPromptEvaluator.__new__(LLMPromptEvaluator)
        evaluator.llm = _FakeLLM()
        evaluator.model = "gpt-oss:20b"
        evaluator.provider = "ollama"
        evaluator.available = True
        results = [
            {
                "prompt": "How are risks assessed?",
                "intent": "feature",
                "coverage": "weak",
                "answerability_score": 20,
                "evidence": [{"url": "https://example.com", "type": "paragraph", "text": "Risk assessment method"}],
            },
            {
                "prompt": "What outcomes should I expect?",
                "intent": "trust",
                "coverage": "weak",
                "answerability_score": 20,
                "evidence": [{"url": "https://example.com", "type": "paragraph", "text": "Expected outcomes"}],
            },
        ]

        response = evaluator.evaluate_results(results)

        self.assertEqual(evaluator.llm.calls, 1)
        self.assertEqual(response["results"][0]["coverage"], "strong")
        self.assertEqual(response["results"][1]["coverage"], "partial")


if __name__ == "__main__":
    unittest.main()
