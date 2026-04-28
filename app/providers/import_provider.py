from abc import ABC, abstractmethod
from pathlib import Path
from typing import List


class ImportProvider(ABC):
    @abstractmethod
    def import_file(self, src_path: Path, category: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def import_folder(self, src_dir: Path, category: str) -> int:
        raise NotImplementedError


class LocalFileImportProvider(ImportProvider):
    def import_file(self, src_path: Path, category: str) -> bool:
        raise NotImplementedError

    def import_folder(self, src_dir: Path, category: str) -> int:
        raise NotImplementedError


class LocalFolderImportProvider(ImportProvider):
    def import_file(self, src_path: Path, category: str) -> bool:
        raise NotImplementedError

    def import_folder(self, src_dir: Path, category: str) -> int:
        raise NotImplementedError


class ChatGPTImportProvider(ImportProvider):
    def import_file(self, src_path: Path, category: str) -> bool:
        raise NotImplementedError

    def import_folder(self, src_dir: Path, category: str) -> int:
        raise NotImplementedError


class NotionImportProvider(ImportProvider):
    def import_file(self, src_path: Path, category: str) -> bool:
        raise NotImplementedError

    def import_folder(self, src_dir: Path, category: str) -> int:
        raise NotImplementedError


class WebImportProvider(ImportProvider):
    def import_file(self, src_path: Path, category: str) -> bool:
        raise NotImplementedError

    def import_folder(self, src_dir: Path, category: str) -> int:
        raise NotImplementedError
