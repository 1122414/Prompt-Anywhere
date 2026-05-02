import json
import logging
from typing import Dict, List, Set

from app.config import config
from app.services.knowledge_base_service import knowledge_base_service

logger = logging.getLogger(__name__)


class TagService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tags_file = config.knowledge_base_dir / "tags.json"
            cls._instance._tag_index: Dict[str, Set[str]] = {}
            cls._instance._ensure_loaded()
        return cls._instance

    def _ensure_loaded(self):
        config.knowledge_base_dir.mkdir(parents=True, exist_ok=True)
        if self._tags_file.exists():
            try:
                with open(self._tags_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._tag_index = {k: set(v) for k, v in data.items()}
            except Exception as e:
                logger.warning(f"Failed to load tags: {e}")
                self._tag_index = {}

    def _save(self):
        try:
            with open(self._tags_file, "w", encoding="utf-8") as f:
                json.dump(
                    {k: list(v) for k, v in self._tag_index.items()},
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
        except Exception as e:
            logger.warning(f"Failed to save tags: {e}")

    def add_tag(self, rel_path: str, tag: str):
        tag = tag.strip()
        if not tag:
            return
        if tag not in self._tag_index:
            self._tag_index[tag] = set()
        self._tag_index[tag].add(rel_path)
        self._save()

    def remove_tag(self, rel_path: str, tag: str):
        tag = tag.strip()
        if tag in self._tag_index:
            self._tag_index[tag].discard(rel_path)
            if not self._tag_index[tag]:
                del self._tag_index[tag]
        self._save()

    def get_tags_for_file(self, rel_path: str) -> List[str]:
        return sorted([t for t, files in self._tag_index.items() if rel_path in files])

    def get_files_for_tag(self, tag: str) -> List[str]:
        return sorted(self._tag_index.get(tag, set()))

    def list_all_tags(self) -> List[str]:
        return sorted(self._tag_index.keys())

    def rename_tag(self, old_tag: str, new_tag: str):
        old_tag = old_tag.strip()
        new_tag = new_tag.strip()
        if old_tag in self._tag_index:
            files = self._tag_index.pop(old_tag)
            self._tag_index[new_tag] = files
            self._save()

    def delete_tag(self, tag: str):
        tag = tag.strip()
        if tag in self._tag_index:
            del self._tag_index[tag]
            self._save()


tag_service = TagService()
