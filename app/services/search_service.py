from typing import List

from app.services.file_service import PromptFile


class SearchService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def search(self, keyword: str, prompts: List[PromptFile], case_insensitive: bool = True) -> List[PromptFile]:
        if not keyword.strip():
            return prompts

        keyword = keyword.strip()
        if case_insensitive:
            keyword = keyword.lower()

        results = []
        for prompt in prompts:
            name = prompt.name.lower() if case_insensitive else prompt.name
            content = prompt.read_content()
            if case_insensitive:
                content = content.lower()

            if keyword in name or keyword in content:
                results.append(prompt)

        return results


search_service = SearchService()
