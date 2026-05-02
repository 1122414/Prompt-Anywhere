import logging
from typing import Dict, List

from app.config import config
from app.services.state_service import state_service

logger = logging.getLogger(__name__)


class SearchRanker:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def calculate_score(
        self,
        keyword: str,
        filename: str,
        category: str,
        content: str,
        path: str,
        filename_pinyin: str = "",
        filename_initials: str = "",
        category_pinyin: str = "",
        category_initials: str = "",
        fuzzy_filename_score: float = 0.0,
        fuzzy_category_score: float = 0.0,
        fuzzy_content_score: float = 0.0,
    ) -> int:
        score = 0
        keyword_lower = keyword.lower()
        filename_lower = filename.lower()
        category_lower = category.lower()

        # 文件名精确匹配
        if keyword_lower in filename_lower:
            if filename_lower == keyword_lower:
                score += 150
            elif filename_lower.startswith(keyword_lower):
                score += 130
            else:
                score += 120

        # 分类名精确匹配
        if keyword_lower in category_lower:
            score += 60

        # 内容精确匹配
        if keyword_lower in content.lower():
            score += 30

        # 拼音匹配
        if config.search_enable_pinyin:
            if filename_pinyin and keyword_lower in filename_pinyin.lower():
                score += 90
            if category_pinyin and keyword_lower in category_pinyin.lower():
                score += 50

        # 首字母匹配
        if config.search_enable_initials:
            if filename_initials and keyword_lower in filename_initials.lower():
                score += 85
            if category_initials and keyword_lower in category_initials.lower():
                score += 45

        # 模糊匹配
        if config.search_enable_fuzzy:
            score += int(fuzzy_filename_score * 0.6)
            score += int(fuzzy_category_score * 0.3)
            score += int(fuzzy_content_score * 0.2)

        # 用户行为加分
        if state_service.is_favorite(path):
            score += 50

        recent_files = state_service.get_recent_files()
        for recent in recent_files:
            if recent.get("path") == path:
                score += 30
                break

        return score


search_ranker = SearchRanker()
