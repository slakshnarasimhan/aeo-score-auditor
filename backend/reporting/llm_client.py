"""Small provider-neutral JSON client for OpenAI and Ollama Cloud models."""
import json
import os
from typing import Any, Dict, Tuple
from urllib.request import Request, urlopen


def openai_disabled() -> bool:
    return os.getenv("DISABLE_OPENAI", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def parse_model_spec(
    model: str,
    default_openai_model: str,
    default_ollama_model: str | None = None,
) -> Tuple[str, str]:
    spec = (model or "").strip()
    if spec.startswith("ollama:"):
        return "ollama", spec.removeprefix("ollama:")
    if spec.startswith("openai:"):
        if openai_disabled():
            return "disabled", spec.removeprefix("openai:")
        return "openai", spec.removeprefix("openai:")
    if spec and spec != "auto":
        if openai_disabled():
            return "disabled", spec
        return "openai", spec
    if os.getenv("OLLAMA_KEY") or os.getenv("OLLAMA_API_KEY"):
        return "ollama", (
            default_ollama_model
            or os.getenv("OLLAMA_CLOUD_MODEL", "qwen3.5:397b")
        )
    if openai_disabled():
        return "disabled", default_openai_model
    return "openai", default_openai_model


class JSONLLMClient:
    """Request a JSON object from either OpenAI or Ollama."""

    def __init__(
        self,
        model: str,
        default_openai_model: str,
        default_ollama_model: str | None = None,
    ):
        self.provider, self.model = parse_model_spec(
            model,
            default_openai_model,
            default_ollama_model,
        )
        self.model_spec = f"{self.provider}:{self.model}"
        self.openai_client = None
        self.ollama_base_url = os.getenv(
            "OLLAMA_BASE_URL", "https://ollama.com"
        ).rstrip("/")
        self.ollama_key = os.getenv("OLLAMA_KEY") or os.getenv("OLLAMA_API_KEY")

        if self.provider == "openai" and not openai_disabled():
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                try:
                    from config import settings

                    api_key = getattr(settings, "OPENAI_API_KEY", None)
                except Exception:
                    api_key = None
            if api_key:
                try:
                    from openai import OpenAI

                    self.openai_client = OpenAI(api_key=api_key)
                except Exception:
                    self.openai_client = None

    def _ollama_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.ollama_key:
            headers["Authorization"] = f"Bearer {self.ollama_key}"
        return headers

    @property
    def available(self) -> bool:
        if self.provider == "disabled":
            return False
        if self.provider == "openai":
            return self.openai_client is not None and not openai_disabled()
        if not self.ollama_key:
            return False
        try:
            request = Request(
                f"{self.ollama_base_url}/api/tags",
                headers=self._ollama_headers(),
            )
            with urlopen(request, timeout=10):
                return True
        except Exception:
            return False

    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
    ) -> Dict[str, Any]:
        if self.provider == "ollama":
            payload = {
                "model": self.model,
                "stream": False,
                "format": "json",
                "think": True,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "options": {
                    "temperature": temperature,
                    "num_ctx": int(os.getenv("OLLAMA_CONTEXT_LENGTH", "16384")),
                },
            }
            request = Request(
                f"{self.ollama_base_url}/api/chat",
                data=json.dumps(payload).encode("utf-8"),
                headers=self._ollama_headers(),
            )
            timeout = int(os.getenv("OLLAMA_REQUEST_TIMEOUT", "90"))
            with urlopen(request, timeout=timeout) as response:
                result = json.load(response)
            content = (result.get("message") or {}).get("content") or "{}"
        else:
            if not self.openai_client:
                raise RuntimeError("OPENAI_API_KEY or OpenAI client is not available")
            response = self.openai_client.chat.completions.create(
                model=self.model,
                temperature=temperature,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            content = response.choices[0].message.content or "{}"

        parsed = _parse_json_object(content)
        if not isinstance(parsed, dict):
            raise ValueError("Model response was not a JSON object")
        return parsed


def _parse_json_object(content: str) -> Dict[str, Any]:
    text = (content or "").strip()
    if text.startswith("```"):
        text = text.strip("`").strip()
        if text.lower().startswith("json"):
            text = text[4:].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        if start < 0:
            raise
        decoder = json.JSONDecoder()
        parsed, _ = decoder.raw_decode(text[start:])
        return parsed
