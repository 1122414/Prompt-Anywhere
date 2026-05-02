import json
import logging
from typing import Dict, List, Optional

import httpx

from app.config import config
from app.providers.llm.base import LLMProvider

logger = logging.getLogger(__name__)


def _parse_json_response(content: str):
    if not content:
        return None
    try:
        json_str = content
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0]
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0]
        return json.loads(json_str.strip())
    except Exception as e:
        logger.warning(f"Failed to parse JSON response: {e}")
        return None


class OpenAICompatibleProvider(LLMProvider):
    def __init__(self):
        self.base_url = config.ai_template_base_url
        self.api_key = config.ai_template_api_key
        self.model = config.ai_template_model

    def is_configured(self) -> bool:
        return bool(self.base_url and self.model)

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.2, timeout: int = 30) -> Optional[str]:
        if not self.is_configured():
            return None

        url = self.base_url.rstrip("/") + "/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }

        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.post(url, json=payload, headers=self._get_headers())
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning(f"OpenAI-compatible API request failed: {e}")
            return None

    def chat_json(self, messages: List[Dict[str, str]], temperature: float = 0.2, timeout: int = 30):
        return _parse_json_response(self.chat(messages, temperature, timeout))


class OllamaProvider(LLMProvider):
    def __init__(self):
        self.base_url = config.ai_template_base_url
        self.model = config.ai_template_model

    def is_configured(self) -> bool:
        return bool(self.base_url and self.model)

    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.2, timeout: int = 30) -> Optional[str]:
        if not self.is_configured():
            return None

        url = self.base_url.rstrip("/") + "/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        }

        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data["message"]["content"]
        except Exception as e:
            logger.warning(f"Ollama API request failed: {e}")
            return None

    def chat_json(self, messages: List[Dict[str, str]], temperature: float = 0.2, timeout: int = 30):
        return _parse_json_response(self.chat(messages, temperature, timeout))
