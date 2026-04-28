import logging
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, List, Optional

from PySide6.QtCore import QThread, Signal

from app.config import config
from app.services.state_service import state_service

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    path: str
    category: str
    filename: str
    matched_fields: List[str] = field(default_factory=list)
    snippets: List[str] = field(default_factory=list)
    score: int = 0


@dataclass
class PromptFileIndexItem:
    path: str
    category: str
    filename: str
    content: str
    modified_time: float


class SearchIndex:
    def __init__(self):
        self._items: List[PromptFileIndexItem] = []
        self._data_dir = config.data_dir

    def rebuild(self):
        self._items = []
        if not self._data_dir.exists():
            return
        for path in self._data_dir.rglob("*"):
            if path.is_file() and path.suffix.lower() in config.supported_prompt_extensions:
                rel = path.relative_to(self._data_dir)
                category = str(rel.parent).replace("\\", "/") if str(rel.parent) != "." else ""
                try:
                    content = path.read_text(encoding=config.file_encoding)
                except Exception as e:
                    logger.warning(f"Failed to read {path}: {e}")
                    content = ""
                self._items.append(PromptFileIndexItem(
                    path=str(rel).replace("\\", "/"),
                    category=category,
                    filename=path.stem,
                    content=content,
                    modified_time=path.stat().st_mtime,
                ))

    def update_file(self, rel_path: str):
        full_path = self._data_dir / rel_path
        if not full_path.exists():
            self._items = [item for item in self._items if item.path != rel_path]
            return
        if full_path.suffix.lower() not in config.supported_prompt_extensions:
            return
        rel = full_path.relative_to(self._data_dir)
        category = str(rel.parent).replace("\\", "/") if str(rel.parent) != "." else ""
        try:
            content = full_path.read_text(encoding=config.file_encoding)
        except Exception as e:
            logger.warning(f"Failed to read {full_path}: {e}")
            content = ""
        self._items = [item for item in self._items if item.path != rel_path]
        self._items.append(PromptFileIndexItem(
            path=str(rel).replace("\\", "/"),
            category=category,
            filename=full_path.stem,
            content=content,
            modified_time=full_path.stat().st_mtime,
        ))

    def remove_file(self, rel_path: str):
        self._items = [item for item in self._items if item.path != rel_path]

    def get_items(self) -> List[PromptFileIndexItem]:
        return self._items


class SearchWorker(QThread):
    results_ready = Signal(int, list)

    def __init__(self, search_id: int, keyword: str, index_items: List[PromptFileIndexItem], case_insensitive: bool = True):
        super().__init__()
        self.search_id = search_id
        self.keyword = keyword
        self.index_items = index_items
        self.case_insensitive = case_insensitive

    def run(self):
        try:
            results = self._do_search()
            self.results_ready.emit(self.search_id, results)
        except Exception as e:
            logger.warning(f"Search worker error: {e}")
            self.results_ready.emit(self.search_id, [])

    def _do_search(self) -> List[SearchResult]:
        keyword = self.keyword.strip()
        if not keyword:
            return []

        search_term = keyword.lower() if self.case_insensitive else keyword
        results = []

        for item in self.index_items:
            matched_fields = []
            score = 0

            name = item.filename.lower() if self.case_insensitive else item.filename
            content = item.content.lower() if self.case_insensitive else item.content

            if search_term in name:
                matched_fields.append("filename")
                score += 100

            content_matches = []
            if search_term in content:
                matched_fields.append("content")
                content_matches = self._find_snippets(item.content, keyword, self.case_insensitive)
                score += len(content_matches) * 10

            if matched_fields:
                if state_service.is_favorite(item.path):
                    score += 50
                recent_files = state_service.get_recent_files()
                for recent in recent_files:
                    if recent.get("path") == item.path:
                        score += 30
                        break

                results.append(SearchResult(
                    path=item.path,
                    category=item.category,
                    filename=item.filename,
                    matched_fields=matched_fields,
                    snippets=content_matches[:3],
                    score=score,
                ))

        results.sort(key=lambda r: r.score, reverse=True)
        max_results = config.search_max_results
        return results[:max_results]

    def _find_snippets(self, content: str, keyword: str, case_insensitive: bool) -> List[str]:
        snippets = []
        radius = config.search_snippet_radius
        text = content.lower() if case_insensitive else content
        search_term = keyword.lower() if case_insensitive else keyword

        for match in re.finditer(re.escape(search_term), text):
            start = max(0, match.start() - radius)
            end = min(len(content), match.end() + radius)
            snippet = content[start:end]
            if start > 0:
                snippet = "..." + snippet
            if end < len(content):
                snippet = snippet + "..."
            snippets.append(snippet)
            if len(snippets) >= 3:
                break

        return snippets


class SearchService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._index = SearchIndex()
            cls._instance._current_search_id = 0
            cls._instance._worker = None
        return cls._instance

    def rebuild_index(self):
        self._index.rebuild()

    def update_index_file(self, rel_path: str):
        self._index.update_file(rel_path)

    def remove_index_file(self, rel_path: str):
        self._index.remove_file(rel_path)

    def search_async(self, keyword: str, case_insensitive: bool = True) -> int:
        self._current_search_id += 1
        search_id = self._current_search_id

        self._worker = SearchWorker(search_id, keyword, self._index.get_items(), case_insensitive)
        return search_id, self._worker

    def get_current_search_id(self) -> int:
        return self._current_search_id


search_service = SearchService()
