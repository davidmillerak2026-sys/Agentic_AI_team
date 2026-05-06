from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Protocol


class LLMClient(Protocol):
    provider: str

    def generate(self, prompt: str) -> str:
        ...


@dataclass
class OfflinePlanner:
    provider: str = "offline"

    def generate(self, prompt: str) -> str:
        return ""


@dataclass
class OpenAICompatibleClient:
    model: str
    base_url: str
    api_key: str
    provider: str = "openai-compatible"
    timeout_seconds: int = 120

    def generate(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a careful AI-native industrial founder-team agent. Return structured, concise output.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        response = post_json(f"{self.base_url.rstrip('/')}/chat/completions", payload, headers=headers)
        choices = response.get("choices", [])
        if not choices:
            return ""
        return str(choices[0]["message"]["content"]).strip()


def create_llm(provider: str = "offline", *, model: str | None = None) -> LLMClient:
    normalized = provider.lower().strip()
    if normalized in {"offline", "deterministic", "extractive"}:
        return OfflinePlanner()
    if normalized in {"openai-compatible", "openai_compatible"}:
        base_url = os.getenv("OPENAI_COMPATIBLE_BASE_URL")
        if not base_url:
            raise ValueError("OPENAI_COMPATIBLE_BASE_URL is required for openai-compatible provider.")
        return OpenAICompatibleClient(
            model=model or os.getenv("OPENAI_COMPATIBLE_MODEL", "local-model"),
            base_url=base_url,
            api_key=os.getenv("OPENAI_COMPATIBLE_API_KEY", ""),
        )
    raise ValueError(f"Unknown provider: {provider}")


def post_json(url: str, payload: dict, *, headers: dict[str, str] | None = None, timeout: int = 120) -> dict:
    data = json.dumps(payload).encode("utf-8")
    request_headers = {"Content-Type": "application/json"}
    request_headers.update(headers or {})
    request = urllib.request.Request(url, data=data, headers=request_headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(f"LLM provider request failed: {exc}") from exc
