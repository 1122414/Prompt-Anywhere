import logging
import shutil
from pathlib import Path
from typing import List, Optional

from app.config import config
from app.constants import AppConstants

logger = logging.getLogger(__name__)


class PromptFile:
    def __init__(self, path: Path):
        self.path = path
        self.name = path.stem
        self.extension = path.suffix.lower()
        self.category = path.parent.name

    def read_content(self) -> str:
        try:
            return self.path.read_text(encoding=config.file_encoding)
        except Exception as e:
            logger.warning(f"Failed to read {self.path}: {e}")
            return ""

    def write_content(self, content: str) -> bool:
        try:
            self.path.write_text(content, encoding=config.file_encoding)
            return True
        except Exception as e:
            logger.warning(f"Failed to write {self.path}: {e}")
            return False


class FileService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._ensure_data_dir()
        return cls._instance

    def _ensure_data_dir(self) -> None:
        config.data_dir.mkdir(parents=True, exist_ok=True)
        config.export_dir.mkdir(parents=True, exist_ok=True)

    def get_categories(self) -> List[str]:
        if not config.data_dir.exists():
            return []
        categories = []
        for item in sorted(config.data_dir.iterdir()):
            if item.is_dir() and not item.name.startswith("."):
                categories.append(item.name)
        return categories

    def get_prompts(self, category: Optional[str] = None) -> List[PromptFile]:
        prompts = []
        if category and category != "全部":
            cat_dir = config.data_dir / category
            if cat_dir.exists():
                for item in sorted(cat_dir.iterdir()):
                    if item.is_file() and item.suffix.lower() in AppConstants.SUPPORTED_EXTENSIONS:
                        prompts.append(PromptFile(item))
        else:
            for cat_dir in config.data_dir.iterdir():
                if cat_dir.is_dir() and not cat_dir.name.startswith("."):
                    for item in sorted(cat_dir.iterdir()):
                        if item.is_file() and item.suffix.lower() in AppConstants.SUPPORTED_EXTENSIONS:
                            prompts.append(PromptFile(item))
        return sorted(prompts, key=lambda p: p.name)

    def create_category(self, name: str) -> bool:
        try:
            cat_dir = config.data_dir / name
            cat_dir.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            logger.warning(f"Failed to create category '{name}': {e}")
            return False

    def rename_category(self, old_name: str, new_name: str) -> bool:
        try:
            old_dir = config.data_dir / old_name
            new_dir = config.data_dir / new_name
            if old_dir.exists():
                old_dir.rename(new_dir)
                return True
            return False
        except Exception as e:
            logger.warning(f"Failed to rename category '{old_name}' -> '{new_name}': {e}")
            return False

    def delete_category(self, name: str) -> bool:
        try:
            cat_dir = config.data_dir / name
            if cat_dir.exists():
                shutil.rmtree(cat_dir)
                return True
            return False
        except Exception as e:
            logger.warning(f"Failed to delete category '{name}': {e}")
            return False

    def create_prompt(self, category: str, name: str, extension: str, content: str = "") -> Optional[PromptFile]:
        try:
            cat_dir = config.data_dir / category
            cat_dir.mkdir(parents=True, exist_ok=True)
            file_path = cat_dir / f"{name}{extension}"
            file_path.write_text(content, encoding=config.file_encoding)
            return PromptFile(file_path)
        except Exception as e:
            logger.warning(f"Failed to create prompt '{name}{extension}': {e}")
            return None

    def rename_prompt(self, prompt_file: PromptFile, new_name: str) -> bool:
        try:
            new_path = prompt_file.path.parent / f"{new_name}{prompt_file.extension}"
            prompt_file.path.rename(new_path)
            prompt_file.path = new_path
            prompt_file.name = new_name
            return True
        except Exception as e:
            logger.warning(f"Failed to rename prompt to '{new_name}': {e}")
            return False

    def delete_prompt(self, prompt_file: PromptFile) -> bool:
        try:
            if prompt_file.path.exists():
                prompt_file.path.unlink()
                return True
            return False
        except Exception as e:
            logger.warning(f"Failed to delete prompt '{prompt_file.path}': {e}")
            return False

    def export_prompt(self, prompt_file: PromptFile, dest_path: Path) -> bool:
        try:
            shutil.copy2(prompt_file.path, dest_path)
            return True
        except Exception as e:
            logger.warning(f"Failed to export prompt to '{dest_path}': {e}")
            return False


file_service = FileService()
