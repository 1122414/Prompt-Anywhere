import logging
import shutil
from pathlib import Path
from typing import Iterator, List, Optional

from app.config import config

logger = logging.getLogger(__name__)


class PromptFile:
    def __init__(self, path: Path):
        self.path = path
        self.name = path.stem
        self.extension = path.suffix.lower()
        self.rel_path = path.relative_to(config.data_dir)

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

    def _resolve_path(self, rel_path: str) -> Path:
        if rel_path:
            return config.data_dir / rel_path
        return config.data_dir

    def iter_all_prompts(self) -> Iterator[PromptFile]:
        if not config.data_dir.exists():
            return
        for path in sorted(config.data_dir.rglob("*")):
            if path.is_file() and path.suffix.lower() in config.supported_prompt_extensions:
                yield PromptFile(path)

    def get_prompts(self, folder_path: str = "") -> List[PromptFile]:
        target_dir = self._resolve_path(folder_path)
        prompts = []
        if target_dir.exists():
            for item in sorted(target_dir.iterdir()):
                if item.is_file() and item.suffix.lower() in config.supported_prompt_extensions:
                    prompts.append(PromptFile(item))
        return sorted(prompts, key=lambda p: p.name)

    def get_categories(self) -> List[str]:
        if not config.data_dir.exists():
            return []
        return sorted([
            d.name for d in config.data_dir.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        ])

    def create_folder(self, parent_path: str, name: str) -> bool:
        try:
            target = self._resolve_path(parent_path) / name
            if target.exists():
                return False
            target.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            logger.warning(f"Failed to create folder '{name}' in '{parent_path}': {e}")
            return False

    def create_prompt(self, parent_path: str, name: str, extension: str, content: str = "") -> Optional[PromptFile]:
        try:
            target_dir = self._resolve_path(parent_path)
            target_dir.mkdir(parents=True, exist_ok=True)
            file_path = target_dir / f"{name}{extension}"
            if file_path.exists():
                return None
            file_path.write_text(content, encoding=config.file_encoding)
            return PromptFile(file_path)
        except Exception as e:
            logger.warning(f"Failed to create prompt '{name}{extension}': {e}")
            return None

    def rename_folder(self, old_path: str, new_name: str) -> bool:
        try:
            old_dir = self._resolve_path(old_path)
            new_dir = old_dir.parent / new_name
            if new_dir.exists():
                return False
            if old_dir.exists():
                old_dir.rename(new_dir)
                return True
            return False
        except Exception as e:
            logger.warning(f"Failed to rename folder '{old_path}' -> '{new_name}': {e}")
            return False

    def delete_folder(self, path: str) -> bool:
        try:
            target = self._resolve_path(path)
            if target.exists():
                shutil.rmtree(target)
                return True
            return False
        except Exception as e:
            logger.warning(f"Failed to delete folder '{path}': {e}")
            return False

    def rename_prompt(self, prompt_file: PromptFile, new_name: str) -> bool:
        try:
            new_path = prompt_file.path.parent / f"{new_name}{prompt_file.extension}"
            if new_path.exists():
                return False
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

    def create_category(self, name: str) -> bool:
        return self.create_folder("", name)

    def rename_category(self, old_name: str, new_name: str) -> bool:
        return self.rename_folder(old_name, new_name)

    def delete_category(self, name: str) -> bool:
        return self.delete_folder(name)

    def import_file(self, src_path: Path, category: str, rename_policy: str = "rename") -> tuple[bool, str]:
        try:
            target_dir = self._resolve_path(category)
            target_dir.mkdir(parents=True, exist_ok=True)
            target_path = target_dir / src_path.name

            if target_path.exists():
                if rename_policy == "skip":
                    return False, f"已跳过: {src_path.name}"
                elif rename_policy == "overwrite":
                    shutil.copy2(str(src_path), str(target_path))
                    return True, str(target_path.relative_to(config.data_dir).as_posix())
                else:
                    stem = src_path.stem
                    ext = src_path.suffix
                    counter = 1
                    while target_path.exists():
                        new_name = f"{stem}_{counter}{ext}"
                        target_path = target_dir / new_name
                        counter += 1
                    shutil.copy2(str(src_path), str(target_path))
                    return True, str(target_path.relative_to(config.data_dir).as_posix())
            else:
                shutil.copy2(str(src_path), str(target_path))
                return True, str(target_path.relative_to(config.data_dir).as_posix())
        except Exception as e:
            logger.warning(f"Failed to import file {src_path}: {e}")
            return False, str(e)

    def import_folder(self, src_dir: Path, category: str, rename_policy: str = "rename") -> tuple[int, list[str]]:
        imported = []
        errors = []
        for path in src_dir.rglob("*"):
            if path.is_file() and path.suffix.lower() in config.supported_prompt_extensions:
                success, msg = self.import_file(path, category, rename_policy)
                if success:
                    imported.append(msg)
                else:
                    errors.append(msg)
        return len(imported), errors


file_service = FileService()
