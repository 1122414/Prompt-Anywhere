from abc import ABC, abstractmethod


class FutureAIService(ABC):
    @abstractmethod
    def suggest_title(self, content: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def suggest_category(self, content: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def optimize_prompt(self, content: str) -> str:
        raise NotImplementedError
