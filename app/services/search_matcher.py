import logging
from dataclasses import dataclass
from typing import List, Optional

from rapidfuzz import fuzz

from app.config import config

logger = logging.getLogger(__name__)


@dataclass
class FuzzyMatchResult:
    score: float
    matched: bool


class SearchMatcher:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _get_threshold(self) -> int:
        mode = config.search_fuzzy_mode
        base = config.search_fuzzy_threshold
        offsets = {"strict": 10, "balanced": 0, "loose": -10}
        return max(0, min(100, base + offsets.get(mode, 0)))

    def fuzzy_match(self, keyword: str, target: str) -> FuzzyMatchResult:
        if not keyword or not target:
            return FuzzyMatchResult(score=0.0, matched=False)

        try:
            score1 = fuzz.partial_ratio(keyword, target)
            score2 = fuzz.token_set_ratio(keyword, target)
            score = max(score1, score2)
            threshold = self._get_threshold()
            return FuzzyMatchResult(
                score=float(score),
                matched=score >= threshold,
            )
        except Exception as e:
            logger.warning(f"Fuzzy match error: {e}")
            return FuzzyMatchResult(score=0.0, matched=False)

    def match_filename(self, keyword: str, filename: str) -> FuzzyMatchResult:
        return self.fuzzy_match(keyword, filename)

    def match_content(self, keyword: str, content: str, max_chars: int = 3000) -> FuzzyMatchResult:
        preview = content[:max_chars] if content else ""
        return self.fuzzy_match(keyword, preview)

    def match_pinyin(self, keyword: str, pinyin_full: str, pinyin_initials: str) -> FuzzyMatchResult:
        if not keyword:
            return FuzzyMatchResult(score=0.0, matched=False)

        scores = []
        if pinyin_full and keyword in pinyin_full:
            scores.append(100.0)
        if pinyin_initials and keyword in pinyin_initials:
            scores.append(95.0)

        if pinyin_full:
            scores.append(fuzz.partial_ratio(keyword, pinyin_full))
        if pinyin_initials:
            scores.append(fuzz.partial_ratio(keyword, pinyin_initials))

        if not scores:
            return FuzzyMatchResult(score=0.0, matched=False)

        score = max(scores)
        return FuzzyMatchResult(
            score=float(score),
            matched=score >= 50,
        )


search_matcher = SearchMatcher()
