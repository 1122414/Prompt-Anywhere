import json
import logging
from datetime import datetime
from typing import Dict

from app.config import config
from app.utils.json_store import JsonFileStore
from app.utils.singleton import Singleton

logger = logging.getLogger(__name__)


class UsageService(Singleton):

    def _init(self):
        self._usage_file = config.knowledge_base_dir / "usage.json"
        self._data: Dict[str, Dict] = {}
        self._ensure_loaded()

    def _ensure_loaded(self):
        config.knowledge_base_dir.mkdir(parents=True, exist_ok=True)
        data = JsonFileStore.load(self._usage_file, {})
        self._data = data if isinstance(data, dict) else {}

    def _save(self):
        JsonFileStore.save(self._usage_file, self._data)

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


usage_service = UsageService()
