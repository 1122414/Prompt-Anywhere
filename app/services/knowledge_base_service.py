import hashlib
import json
import logging
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from app.config import config

logger = logging.getLogger(__name__)


@dataclass
class PromptMetadata:
    id: str = ""
    path: str = ""
    title: str = ""
    tags: List[str] = field(default_factory=list)
    summary: str = ""
    created_at: str = ""
    updated_at: str = ""
    last_used_at: Optional[str] = None
    copy_count: int = 0
    favorite: bool = False
    rating: int = 0
    content_hash: str = ""
    embedding_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PromptMetadata":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class KnowledgeBaseService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._kb_dir = config.knowledge_base_dir
            cls._instance._metadata_file = cls._instance._kb_dir / "metadata.json"
            cls._instance._items: Dict[str, PromptMetadata] = {}
            cls._initialized = False
        return cls._instance

    def ensure_initialized(self):
        if self._initialized:
            return
        self._kb_dir.mkdir(parents=True, exist_ok=True)
        if self._metadata_file.exists():
            self._load_metadata()
        else:
            self._save_metadata()
        self._initialized = True

    def _load_metadata(self):
        try:
            with open(self._metadata_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and "items" in data:
                self._items = {
                    k: PromptMetadata.from_dict(v)
                    for k, v in data["items"].items()
                }
        except Exception as e:
            logger.warning(f"Failed to load metadata: {e}")
            self._items = {}

    def _save_metadata(self):
        try:
            self._kb_dir.mkdir(parents=True, exist_ok=True)
            with open(self._metadata_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "version": 1,
                        "items": {k: v.to_dict() for k, v in self._items.items()},
                    },
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
        except Exception as e:
            logger.warning(f"Failed to save metadata: {e}")

    def _compute_content_hash(self, content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]

    def sync_file(self, rel_path: str, content: str = ""):
        self.ensure_initialized()
        existing = self._items.get(rel_path)
        content_hash = self._compute_content_hash(content)

        if existing:
            if existing.content_hash == content_hash:
                return
            existing.content_hash = content_hash
            existing.updated_at = self._now_iso()
            self._save_metadata()
        else:
            meta = PromptMetadata(
                id=hashlib.sha256(rel_path.encode()).hexdigest()[:12],
                path=rel_path,
                title=Path(rel_path).stem,
                content_hash=content_hash,
                created_at=self._now_iso(),
                updated_at=self._now_iso(),
            )
            self._items[rel_path] = meta
            self._save_metadata()

    def remove_file(self, rel_path: str):
        self.ensure_initialized()
        if rel_path in self._items:
            del self._items[rel_path]
            self._save_metadata()

    def get_metadata(self, rel_path: str) -> Optional[PromptMetadata]:
        self.ensure_initialized()
        return self._items.get(rel_path)

    def set_metadata(self, rel_path: str, meta: PromptMetadata):
        self.ensure_initialized()
        self._items[rel_path] = meta
        self._save_metadata()

    def update_field(self, rel_path: str, field_name: str, value: Any):
        self.ensure_initialized()
        meta = self._items.get(rel_path)
        if meta and hasattr(meta, field_name):
            setattr(meta, field_name, value)
            meta.updated_at = self._now_iso()
            self._save_metadata()

    def full_sync(self):
        self.ensure_initialized()
        data_dir = config.data_dir
        if not data_dir.exists():
            return

        current_paths: Set[str] = set()
        for path in data_dir.rglob("*"):
            if path.is_file() and path.suffix.lower() in config.supported_prompt_extensions:
                rel = str(path.relative_to(data_dir)).replace("\\", "/")
                current_paths.add(rel)
                try:
                    content = path.read_text(encoding=config.file_encoding)
                except Exception:
                    content = ""
                self.sync_file(rel, content)

        stale = [k for k in self._items if k not in current_paths]
        for k in stale:
            del self._items[k]
        if stale:
            self._save_metadata()

    def list_all(self) -> List[PromptMetadata]:
        self.ensure_initialized()
        return list(self._items.values())

    @staticmethod
    def _now_iso() -> str:
        from datetime import datetime
        return datetime.now().isoformat()


knowledge_base_service = KnowledgeBaseService()
