from __future__ import annotations

import json
from typing import Any

import httpx

from app.agent.prompts import EXTRACTION_PROMPT, SYSTEM_SCIENTIST
from app.config.settings import get_settings


class LLMClient:
    def available(self) -> bool:
        settings = get_settings()
        return bool(settings.openai_api_key)

    def complete(self, prompt: str, system: str = SYSTEM_SCIENTIST) -> str | None:
        settings = get_settings()
        if not settings.openai_api_key:
            return None
        payload = {
            "model": settings.openai_model,
            "temperature": 0.1,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        }
        headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
        url = settings.openai_base_url.rstrip("/") + "/chat/completions"
        try:
            response = httpx.post(url, headers=headers, json=payload, timeout=45.0)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception:
            return None

    def extract_json(self, message: str) -> dict[str, Any] | None:
        raw = self.complete(f"{EXTRACTION_PROMPT}\n\nUser message:\n{message}")
        if not raw:
            return None
        start = raw.find("{")
        end = raw.rfind("}")
        if start < 0 or end < 0:
            return None
        try:
            data = json.loads(raw[start : end + 1])
        except json.JSONDecodeError:
            return None
        return data if isinstance(data, dict) else None
