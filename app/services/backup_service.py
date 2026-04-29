import json
import logging
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

logger = logging.getLogger(__name__)


class BackupService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._backup_dir = None
            cls._instance._metadata_path = None
        return cls._instance

    def initialize(self, backup_dir: Path):
        self._backup_dir = backup_dir
        self._metadata_path = backup_dir / "metadata.json"
        backup_dir.mkdir(parents=True, exist_ok=True)

    def _load_metadata(self) -> dict:
        if self._metadata_path and self._metadata_path.exists():
            try:
                return json.loads(self._metadata_path.read_text(encoding="utf-8"))
            except Exception:
                logger.warning("Failed to load backup metadata")
        return {"last_backup_time": None, "backup_count": 0}

    def _save_metadata(self, metadata: dict):
        if self._metadata_path:
            try:
                self._metadata_path.write_text(
                    json.dumps(metadata, indent=2, ensure_ascii=False),
                    encoding="utf-8"
                )
            except Exception:
                logger.warning("Failed to save backup metadata")

    def create_backup(self, data_dir: Path, config_path: Path, state_path: Path) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}.zip"
        backup_path = self._backup_dir / backup_name
        counter = 1
        while backup_path.exists():
            backup_name = f"backup_{timestamp}_{counter}.zip"
            backup_path = self._backup_dir / backup_name
            counter += 1

        try:
            with ZipFile(backup_path, "w", ZIP_DEFLATED) as zf:
                if data_dir.exists():
                    for file_path in data_dir.rglob("*"):
                        if file_path.is_file():
                            arcname = f"data/{file_path.relative_to(data_dir)}"
                            zf.write(file_path, arcname)

                if config_path.exists():
                    zf.write(config_path, "app_config.json")

                if state_path.exists():
                    zf.write(state_path, "app_state.json")

            metadata = self._load_metadata()
            metadata["last_backup_time"] = datetime.now().isoformat()
            metadata["backup_count"] = len(list(self._backup_dir.glob("backup_*.zip")))
            self._save_metadata(metadata)

            logger.info(f"Backup created: {backup_name}")
            return backup_path
        except Exception as e:
            logger.warning(f"Failed to create backup: {e}")
            if backup_path.exists():
                backup_path.unlink()
            raise

    def list_backups(self) -> list[dict]:
        backups = []
        if not self._backup_dir or not self._backup_dir.exists():
            return backups

        for path in sorted(self._backup_dir.glob("backup_*.zip"), reverse=True):
            stat = path.stat()
            backups.append({
                "path": path,
                "size": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })
        return backups

    def restore_backup(self, backup_path: Path, data_dir: Path) -> bool:
        if not backup_path.exists():
            logger.warning(f"Backup file not found: {backup_path}")
            return False

        try:
            with ZipFile(backup_path, "r") as zf:
                zf.extractall(data_dir.parent)
            logger.info(f"Backup restored from: {backup_path.name}")
            return True
        except Exception as e:
            logger.warning(f"Failed to restore backup: {e}")
            return False

    def cleanup_old_backups(self, max_count: int = 20):
        backups = sorted(
            self._backup_dir.glob("backup_*.zip"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        for old_backup in backups[max_count:]:
            try:
                old_backup.unlink()
                logger.info(f"Removed old backup: {old_backup.name}")
            except Exception as e:
                logger.warning(f"Failed to remove old backup {old_backup.name}: {e}")

        metadata = self._load_metadata()
        metadata["backup_count"] = len(list(self._backup_dir.glob("backup_*.zip")))
        self._save_metadata(metadata)

    def should_auto_backup(self, interval_hours: int = 24) -> bool:
        metadata = self._load_metadata()
        last_time_str = metadata.get("last_backup_time")
        if not last_time_str:
            return True

        try:
            last_time = datetime.fromisoformat(last_time_str)
            elapsed = datetime.now() - last_time
            return elapsed.total_seconds() >= interval_hours * 3600
        except Exception:
            return True

    def get_last_backup_time(self) -> datetime | None:
        metadata = self._load_metadata()
        last_time_str = metadata.get("last_backup_time")
        if last_time_str:
            try:
                return datetime.fromisoformat(last_time_str)
            except Exception:
                pass

        backups = self.list_backups()
        if backups:
            return datetime.fromisoformat(backups[0]["created_at"])
        return None


backup_service = BackupService()
