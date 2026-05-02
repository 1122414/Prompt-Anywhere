import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from PySide6.QtCore import QThread, Signal

from app.config import config
from app.services.pinyin_service import pinyin_service
from app.services.search_matcher import FuzzyMatchResult, search_matcher
from app.services.search_ranker import search_ranker
from app.services.semantic_search_service import semantic_search_service
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
    filename_pinyin: str = ""
    filename_initials: str = ""
    category_pinyin: str = ""
    category_initials: str = ""
    content_preview: str = ""


class SearchIndex:
    def __init__(self):
        self._items: List[PromptFileIndexItem] = []
        self._data_dir = config.data_dir

    def _build_item(self, path: Path, rel: Path) -> PromptFileIndexItem:
        category = str(rel.parent).replace("\\", "/") if str(rel.parent) != "." else ""
        try:
            content = path.read_text(encoding=config.file_encoding)
        except Exception as e:
            logger.warning(f"Failed to read {path}: {e}")
            content = ""

        filename_pinyin = ""
        filename_initials = ""
        category_pinyin = ""
        category_initials = ""

        if config.search_enable_pinyin or config.search_enable_initials:
            filename_fields = pinyin_service.build_pinyin_fields(path.stem)
            filename_pinyin = filename_fields.get("full", "")
            filename_initials = filename_fields.get("initials", "")

            if category:
                category_fields = pinyin_service.build_pinyin_fields(category)
                category_pinyin = category_fields.get("full", "")
                category_initials = category_fields.get("initials", "")

        content_preview = content[:3000] if content else ""

        return PromptFileIndexItem(
            path=str(rel).replace("\\", "/"),
            category=category,
            filename=path.stem,
            content=content,
            modified_time=path.stat().st_mtime,
            filename_pinyin=filename_pinyin,
            filename_initials=filename_initials,
            category_pinyin=category_pinyin,
            category_initials=category_initials,
            content_preview=content_preview,
        )

    def rebuild(self):
        self._items = []
        if not self._data_dir.exists():
            return
        for path in self._data_dir.rglob("*"):
            if path.is_file() and path.suffix.lower() in config.supported_prompt_extensions:
                rel = path.relative_to(self._data_dir)
                try:
                    item = self._build_item(path, rel)
                    self._items.append(item)
                except Exception as e:
                    logger.warning(f"Failed to index {path}: {e}")

    def update_file(self, rel_path: str):
        full_path = self._data_dir / rel_path
        if not full_path.exists():
            self._items = [item for item in self._items if item.path != rel_path]
            return
        if full_path.suffix.lower() not in config.supported_prompt_extensions:
            return
        rel = full_path.relative_to(self._data_dir)
        try:
            item = self._build_item(full_path, rel)
            self._items = [i for i in self._items if i.path != rel_path]
            self._items.append(item)
        except Exception as e:
            logger.warning(f"Failed to update index for {rel_path}: {e}")

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
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            results = self._do_search()
            if not self._cancelled:
                self.results_ready.emit(self.search_id, results)
        except Exception as e:
            logger.warning(f"Search worker error: {e}")
            if not self._cancelled:
                self.results_ready.emit(self.search_id, [])
        finally:
            self._cancelled = True

    def _do_search(self) -> List[SearchResult]:
        keyword = self.keyword.strip()
        if not keyword:
            return []

        search_term = keyword.lower() if self.case_insensitive else keyword
        results = []
        first_paint = config.search_first_paint_results
        max_results = config.search_max_results

        for item in self.index_items:
            if self._cancelled:
                return []

            matched_fields = []
            score = 0

            name = item.filename.lower() if self.case_insensitive else item.filename
            content = item.content.lower() if self.case_insensitive else item.content

            fuzzy_filename = FuzzyMatchResult(0.0, False)
            fuzzy_category = FuzzyMatchResult(0.0, False)
            fuzzy_content = FuzzyMatchResult(0.0, False)

            if config.search_enable_fuzzy:
                fuzzy_filename = search_matcher.match_filename(search_term, name)
                fuzzy_category = search_matcher.match_filename(search_term, item.category.lower())
                fuzzy_content = search_matcher.match_content(search_term, item.content_preview)

            has_exact_match = (
                search_term in name
                or search_term in content
                or search_term in item.category.lower()
            )

            has_pinyin_match = False
            if config.search_enable_pinyin or config.search_enable_initials:
                pinyin_result = search_matcher.match_pinyin(
                    search_term,
                    item.filename_pinyin.lower(),
                    item.filename_initials.lower(),
                )
                has_pinyin_match = pinyin_result.matched
                if has_pinyin_match:
                    matched_fields.append("pinyin")

            has_fuzzy_match = (
                config.search_enable_fuzzy
                and (fuzzy_filename.matched or fuzzy_category.matched or fuzzy_content.matched)
            )

            if has_exact_match or has_pinyin_match or has_fuzzy_match:
                if search_term in name:
                    matched_fields.append("filename")
                if search_term in content:
                    matched_fields.append("content")
                if search_term in item.category.lower():
                    matched_fields.append("category")

                if fuzzy_filename.matched:
                    matched_fields.append("fuzzy_filename")
                if fuzzy_content.matched:
                    matched_fields.append("fuzzy_content")

                content_matches = []
                if "content" in matched_fields or "fuzzy_content" in matched_fields:
                    content_matches = self._find_snippets(item.content, keyword, self.case_insensitive)

                score = search_ranker.calculate_score(
                    keyword=keyword,
                    filename=item.filename,
                    category=item.category,
                    content=item.content,
                    path=item.path,
                    filename_pinyin=item.filename_pinyin,
                    filename_initials=item.filename_initials,
                    category_pinyin=item.category_pinyin,
                    category_initials=item.category_initials,
                    fuzzy_filename_score=fuzzy_filename.score,
                    fuzzy_category_score=fuzzy_category.score,
                    fuzzy_content_score=fuzzy_content.score,
                )

                results.append(SearchResult(
                    path=item.path,
                    category=item.category,
                    filename=item.filename,
                    matched_fields=matched_fields,
                    snippets=content_matches[:3],
                    score=score,
                ))

        if config.semantic_search_enabled and not self._cancelled:
            semantic_results = semantic_search_service.search(keyword)
            semantic_scores = {path: score for path, score in semantic_results}
            for result in results:
                semantic_score = semantic_scores.get(result.path, 0.0)
                if semantic_score > 0:
                    result.matched_fields.append("semantic")
                    result.score = int(result.score * 0.75 + semantic_score * 100 * 0.25)

        results.sort(key=lambda r: r.score, reverse=True)
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

    def search_async(self, keyword: str, case_insensitive: bool = True):
        if self._worker is not None:
            try:
                self._worker.cancel()
                try:
                    self._worker.results_ready.disconnect()
                except Exception:
                    pass
            except RuntimeError:
                pass
            self._worker = None

        self._current_search_id += 1
        search_id = self._current_search_id

        self._worker = SearchWorker(search_id, keyword, self._index.get_items(), case_insensitive)
        return search_id, self._worker

    def get_current_search_id(self) -> int:
        return self._current_search_id


search_service = SearchService()
