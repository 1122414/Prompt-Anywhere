import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

import httpx
import numpy as np

from app.config import config

logger = logging.getLogger(__name__)


class EmbeddingService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        api_key = config.semantic_search_api_key
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        return headers

    def embed_texts(self, texts: List[str]) -> Optional[np.ndarray]:
        if not texts:
            return None

        provider = config.semantic_search_provider
        if provider == "api":
            return self._embed_via_api(texts)
        return None

    def _embed_via_api(self, texts: List[str]) -> Optional[np.ndarray]:
        base_url = config.semantic_search_api_base_url
        model = config.semantic_search_api_model

        if not base_url:
            logger.warning("Semantic search API base URL not configured")
            return None

        url = base_url.rstrip("/") + "/embeddings"
        payload = {"model": model, "input": texts}

        try:
            with httpx.Client(timeout=60.0) as client:
                resp = client.post(url, json=payload, headers=self._get_headers())
                resp.raise_for_status()
                data = resp.json()
                embeddings = [item["embedding"] for item in data["data"]]
                return np.array(embeddings, dtype=np.float32)
        except Exception as e:
            logger.warning(f"Embedding API request failed: {e}")
            return None

    def embed_query(self, text: str) -> Optional[np.ndarray]:
        result = self.embed_texts([text])
        if result is not None and len(result) > 0:
            return result[0]
        return None


embedding_service = EmbeddingService()
