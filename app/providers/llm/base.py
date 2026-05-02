import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.2, timeout: int = 30) -> Optional[str]:
        raise NotImplementedError

    @abstractmethod
    def chat_json(self, messages: List[Dict[str, str]], temperature: float = 0.2, timeout: int = 30) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def is_configured(self) -> bool:
        raise NotImplementedError
