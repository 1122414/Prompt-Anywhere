import json
import logging
from datetime import datetime
from typing import Dict, Optional

from app.config import config

logger = logging.getLogger(__name__)


class UsageService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._usage_file = config.knowledge_base_dir / "usage.json"
            cls._instance._data: Dict[str, Dict] = {}
            cls._instance._ensure_loaded()
        return cls._instance

    def _ensure_loaded(self):
        config.knowledge_base_dir.mkdir(parents=True, exist_ok=True)
        if self._usage_file.exists():
            try:
                with open(self._usage_file, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
                if not isinstance(self._data, dict):
                    self._data = {}
            except Exception as e:
                logger.warning(f"Failed to load usage data: {e}")
                self._data = {}

    def _save(self):
        try:
            with open(self._usage_file, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save usage data: {e}")

    def record_copy(self, rel_path: str):
        if rel_path not in self._data:
            self._data[rel_path] = {"copy_count": 0, "last_used_at": None, "rating": 0}
        self._data[rel_path]["copy_count"] = self._data[rel_path].get("copy_count", 0) + 1
        self._data[rel_path]["last_used_at"] = datetime.now().isoformat()
        self._save()

    def set_rating(self, rel_path: str, rating: int):
        rating = max(0, min(5, rating))
        if rel_path not in self._data:
            self._data[rel_path] = {"copy_count": 0, "last_used_at": None, "rating": 0}
        self._data[rel_path]["rating"] = rating
        self._save()

    def get_stats(self, rel_path: str) -> Dict:
        return self._data.get(rel_path, {"copy_count": 0, "last_used_at": None, "rating": 0})

    def remove_file(self, rel_path: str):
        if rel_path in self._data:
            del self._data[rel_path]
            self._save()


usage_service = UsageService()
