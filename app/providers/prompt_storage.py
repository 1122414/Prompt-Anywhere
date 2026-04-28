from abc import ABC, abstractmethod


class PromptStorage(ABC):
    @abstractmethod
    def list_categories(self):
        raise NotImplementedError

    @abstractmethod
    def list_prompts(self, category=None):
        raise NotImplementedError

    @abstractmethod
    def read_prompt(self, path):
        raise NotImplementedError

    @abstractmethod
    def write_prompt(self, path, content):
        raise NotImplementedError

    @abstractmethod
    def delete_prompt(self, path):
        raise NotImplementedError

    @abstractmethod
    def move_prompt(self, src, dst):
        raise NotImplementedError


class FileSystemPromptStorage(PromptStorage):
    def list_categories(self):
        raise NotImplementedError

    def list_prompts(self, category=None):
        raise NotImplementedError

    def read_prompt(self, path):
        raise NotImplementedError

    def write_prompt(self, path, content):
        raise NotImplementedError

    def delete_prompt(self, path):
        raise NotImplementedError

    def move_prompt(self, src, dst):
        raise NotImplementedError


class DatabasePromptStorage(PromptStorage):
    def list_categories(self):
        raise NotImplementedError

    def list_prompts(self, category=None):
        raise NotImplementedError

    def read_prompt(self, path):
        raise NotImplementedError

    def write_prompt(self, path, content):
        raise NotImplementedError

    def delete_prompt(self, path):
        raise NotImplementedError

    def move_prompt(self, src, dst):
        raise NotImplementedError


class CloudPromptStorage(PromptStorage):
    def list_categories(self):
        raise NotImplementedError

    def list_prompts(self, category=None):
        raise NotImplementedError

    def read_prompt(self, path):
        raise NotImplementedError

    def write_prompt(self, path, content):
        raise NotImplementedError

    def delete_prompt(self, path):
        raise NotImplementedError

    def move_prompt(self, src, dst):
        raise NotImplementedError
