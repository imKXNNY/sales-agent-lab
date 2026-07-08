"""OpenAI-compatible LLM client wrapper."""

from typing import Any

import httpx

from sales_agent_lab.config import settings


class LlmClient:
    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        default_model: str | None = None,
    ) -> None:
        self.base_url = (base_url or settings.llm_base_url).rstrip("/")
        self.api_key = api_key or settings.llm_api_key
        self.default_model = default_model or settings.llm_default_model
        self._headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        response_format: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "model": model or self.default_model,
            "messages": messages,
            "temperature": temperature if temperature is not None else settings.llm_temperature,
            "max_tokens": max_tokens if max_tokens is not None else settings.llm_max_tokens,
        }
        if response_format:
            body["response_format"] = response_format
        with httpx.Client(timeout=120.0, headers=self._headers) as client:
            resp = client.post(f"{self.base_url}/chat/completions", json=body)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str | None = None,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return self.chat(messages, model=model, response_format=response_format)["content"]
