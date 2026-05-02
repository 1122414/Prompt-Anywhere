import logging
from typing import List

from app.config import config
from app.services.embedding_service import embedding_service
from app.services.vector_store import vector_store

logger = logging.getLogger(__name__)


class SemanticSearchService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def is_enabled(self) -> bool:
        return config.semantic_search_enabled

    def search(self, keyword: str) -> List[tuple]:
        if not self.is_enabled():
            return []

        query_embedding = embedding_service.embed_query(keyword)
        if query_embedding is None:
            return []

        results = vector_store.search(query_embedding, top_k=config.semantic_search_top_k)
        return results

    def build_index(self, texts: List[str], paths: List[str]) -> bool:
        if not texts or not paths:
            return False

        logger.info(f"Building semantic index for {len(texts)} items...")
        embeddings = embedding_service.embed_texts(texts)
        if embeddings is None:
            logger.warning("Failed to generate embeddings")
            return False

        vector_store.build_index(paths, embeddings)
        logger.info(f"Semantic index built: {len(paths)} items")
        return True

    def get_index_status(self) -> dict:
        return {
            "enabled": self.is_enabled(),
            "provider": config.semantic_search_provider,
            "item_count": vector_store.get_item_count(),
        }


semantic_search_service = SemanticSearchService()
