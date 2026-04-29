import logging
from pathlib import Path
from typing import List, Tuple

from app.config import config

logger = logging.getLogger(__name__)


class ComposerService:
    _instance = None
    _files: list[str]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._files = []
        return cls._instance

    def _resolve_rel(self, path: str) -> str:
        p = Path(path)
        try:
            return str(p.relative_to(config.data_dir).as_posix())
        except ValueError:
            return str(p.as_posix())

    def add_file(self, path: str) -> bool:
        rel = self._resolve_rel(path)
        if rel in self._files:
            return False
        self._files.append(rel)
        return True

    def remove_file(self, path: str) -> bool:
        rel = self._resolve_rel(path)
        try:
            self._files.remove(rel)
            return True
        except ValueError:
            return False

    def move_up(self, index: int) -> bool:
        if index <= 0 or index >= len(self._files):
            return False
        self._files[index], self._files[index - 1] = self._files[index - 1], self._files[index]
        return True

    def move_down(self, index: int) -> bool:
        if index < 0 or index >= len(self._files) - 1:
            return False
        self._files[index], self._files[index + 1] = self._files[index + 1], self._files[index]
        return True

    def clear(self) -> None:
        self._files.clear()

    def get_files(self) -> List[str]:
        return list(self._files)

    def build(self) -> str:
        if not self._files:
            return ""

        parts = []
        separator = config.composer_separator
        include_title = config.composer_include_file_title
        title_level = config.composer_title_level

        for rel_path in self._files:
            full_path = config.data_dir / rel_path
            if not full_path.exists():
                logger.warning(f"File not found: {rel_path}")
                continue
            content = full_path.read_text(encoding=config.file_encoding)
            if include_title:
                header = f"{'#' * title_level} {Path(rel_path).stem}"
                content = f"{header}\n\n{content}"
            parts.append(content)

        return separator.join(parts)

    def save(self, name: str) -> Tuple[bool, str]:
        content = self.build()
        if not content:
            return False, "No content to save"
        try:
            save_dir = config.composer_save_dir
            save_dir.mkdir(parents=True, exist_ok=True)
            file_path = save_dir / f"{name}.md"
            file_path.write_text(content, encoding=config.file_encoding)
            return True, str(file_path)
        except Exception as e:
            logger.warning(f"Failed to save composed content: {e}")
            return False, str(e)

    def export(self, dest_path: Path) -> Tuple[bool, str]:
        content = self.build()
        if not content:
            return False, "No content to export"
        try:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            dest_path.write_text(content, encoding=config.file_encoding)
            return True, str(dest_path)
        except Exception as e:
            logger.warning(f"Failed to export composed content: {e}")
            return False, str(e)


composer_service = ComposerService()
