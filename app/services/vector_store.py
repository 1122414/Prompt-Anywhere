import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from app.config import config

logger = logging.getLogger(__name__)


class VectorStore:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._index_dir = config.knowledge_base_dir / "vector_index"
            cls._instance._embeddings_file = cls._instance._index_dir / "embeddings.npy"
            cls._instance._items_file = cls._instance._index_dir / "items.json"
            cls._instance._embeddings: Optional[np.ndarray] = None
            cls._instance._items: List[str] = []
            cls._instance._loaded = False
        return cls._instance

    def _ensure_dir(self):
        self._index_dir.mkdir(parents=True, exist_ok=True)

    def _load(self):
        if self._loaded:
            return
        self._ensure_dir()
        if self._embeddings_file.exists():
            try:
                self._embeddings = np.load(self._embeddings_file)
            except Exception as e:
                logger.warning(f"Failed to load embeddings: {e}")
                self._embeddings = None
        if self._items_file.exists():
            try:
                with open(self._items_file, "r", encoding="utf-8") as f:
                    self._items = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load vector items: {e}")
                self._items = []
        self._loaded = True

    def save(self):
        self._ensure_dir()
        if self._embeddings is not None:
            try:
                np.save(self._embeddings_file, self._embeddings)
            except Exception as e:
                logger.warning(f"Failed to save embeddings: {e}")
        try:
            with open(self._items_file, "w", encoding="utf-8") as f:
                json.dump(self._items, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save vector items: {e}")

    def build_index(self, items: List[str], embeddings: np.ndarray):
        self._items = items
        self._embeddings = embeddings
        self._loaded = True
        self.save()

    def search(self, query_embedding: np.ndarray, top_k: int = 20) -> List[Tuple[str, float]]:
        self._load()
        if self._embeddings is None or len(self._items) == 0:
            return []

        query_norm = query_embedding / (np.linalg.norm(query_embedding) + 1e-8)
        embeddings_norm = self._embeddings / (np.linalg.norm(self._embeddings, axis=1, keepdims=True) + 1e-8)
        similarities = np.dot(embeddings_norm, query_norm)

        top_indices = np.argsort(similarities)[::-1][:top_k]
        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            if score >= config.semantic_search_min_score:
                results.append((self._items[idx], score))
        return results

    def get_item_count(self) -> int:
        self._load()
        return len(self._items)

    def clear(self):
        self._embeddings = None
        self._items = []
        self._loaded = True
        if self._embeddings_file.exists():
            try:
                self._embeddings_file.unlink()
            except Exception as e:
                logger.warning(f"Failed to remove embeddings file: {e}")
        if self._items_file.exists():
            try:
                self._items_file.unlink()
            except Exception as e:
                logger.warning(f"Failed to remove items file: {e}")


vector_store = VectorStore()
