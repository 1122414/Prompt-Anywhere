import logging
from datetime import datetime
from pathlib import Path

from app.config import config

logger = logging.getLogger(__name__)


class HistoryService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_history_dir(self, file_path: Path) -> Path:
        return file_path.parent / ".history" / file_path.stem

    def create_version(self, file_path: Path, content: str) -> bool:
        if not file_path.exists():
            return False

        try:
            current_content = file_path.read_text(encoding=config.file_encoding)
        except Exception as e:
            logger.warning(f"Failed to read current file for versioning: {file_path}: {e}")
            return False

        if current_content == content:
            return False

        try:
            history_dir = self.get_history_dir(file_path)
            history_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            version_name = f"{timestamp}{file_path.suffix}"
            version_path = history_dir / version_name

            version_path.write_text(current_content, encoding=config.file_encoding)

            self.cleanup_old_versions(file_path)

            logger.debug(f"Created history version: {version_path}")
            return True
        except Exception as e:
            logger.warning(f"Failed to create version for {file_path}: {e}")
            return False

    def list_versions(self, file_path: Path) -> list[dict]:
        history_dir = self.get_history_dir(file_path)
        if not history_dir.exists():
            return []

        versions = []
        try:
            for version_file in sorted(history_dir.iterdir(), reverse=True):
                if version_file.is_file():
                    stat = version_file.stat()
                    versions.append({
                        "path": version_file,
                        "created_at": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                        "size": stat.st_size,
                    })
        except Exception as e:
            logger.warning(f"Failed to list versions for {file_path}: {e}")

        return versions

    def get_version_content(self, version_path: Path) -> str:
        try:
            return version_path.read_text(encoding=config.file_encoding)
        except Exception as e:
            logger.warning(f"Failed to read version {version_path}: {e}")
            return ""

    def restore_version(self, file_path: Path, version_path: Path) -> bool:
        if not version_path.exists():
            logger.warning(f"Version file not found: {version_path}")
            return False

        try:
            if file_path.exists():
                history_dir = self.get_history_dir(file_path)
                history_dir.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = history_dir / f"{timestamp}{file_path.suffix}"
                backup_path.write_text(
                    file_path.read_text(encoding=config.file_encoding),
                    encoding=config.file_encoding,
                )
                self.cleanup_old_versions(file_path)

            content = version_path.read_text(encoding=config.file_encoding)
            file_path.write_text(content, encoding=config.file_encoding)

            logger.debug(f"Restored version {version_path} to {file_path}")
            return True
        except Exception as e:
            logger.warning(f"Failed to restore version {version_path} to {file_path}: {e}")
            return False

    def cleanup_old_versions(self, file_path: Path, max_count: int = 20):
        history_dir = self.get_history_dir(file_path)
        if not history_dir.exists():
            return

        try:
            versions = sorted(
                [f for f in history_dir.iterdir() if f.is_file()],
                key=lambda f: f.name,
                reverse=True,
            )
            for old_version in versions[max_count:]:
                old_version.unlink()
                logger.debug(f"Removed old version: {old_version}")
        except Exception as e:
            logger.warning(f"Failed to cleanup versions for {file_path}: {e}")


history_service = HistoryService()
