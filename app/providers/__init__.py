from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List


@dataclass
class SearchOptions:
    case_insensitive: bool = True
    max_results: int = 100
    highlight: bool = True


@dataclass
class SearchResult:
    path: str
    category: str
    filename: str
    matched_fields: List[str]
    snippets: List[str]
    score: int = 0


class SearchProvider(ABC):
    @abstractmethod
    def search(self, query: str, options: SearchOptions) -> List[SearchResult]:
        raise NotImplementedError


class KeywordSearchProvider(SearchProvider):
    def search(self, query: str, options: SearchOptions) -> List[SearchResult]:
        raise NotImplementedError


class EmbeddingSearchProvider(SearchProvider):
    def search(self, query: str, options: SearchOptions) -> List[SearchResult]:
        raise NotImplementedError


class VectorSearchProvider(SearchProvider):
    def search(self, query: str, options: SearchOptions) -> List[SearchResult]:
        raise NotImplementedError


class AISearchProvider(SearchProvider):
    def search(self, query: str, options: SearchOptions) -> List[SearchResult]:
        raise NotImplementedError
