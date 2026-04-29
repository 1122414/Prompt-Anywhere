import json
import logging
import os
import platform
import zipfile
from datetime import datetime
from pathlib import Path

from app.config import config

logger = logging.getLogger(__name__)


class DiagnosticsService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def export_diagnostics(self, output_path: Path) -> bool:
        try:
            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
                self._add_system_info(zf)
                self._add_config(zf)
                self._add_state(zf)
                self._add_logs(zf)
            return True
        except Exception as e:
            logger.warning(f"Failed to export diagnostics: {e}")
            return False

    def _add_system_info(self, zf: zipfile.ZipFile):
        info = {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "app_name": config.app_name,
            "app_version": config.app_version,
            "app_env": config.app_env,
            "timestamp": datetime.now().isoformat(),
        }
        zf.writestr("system_info.json", json.dumps(info, indent=2, ensure_ascii=False))

    def _add_config(self, zf: zipfile.ZipFile):
        config_path = Path("app_config.json")
        if config_path.exists():
            zf.write(config_path, "app_config.json")

    def _add_state(self, zf: zipfile.ZipFile):
        state_path = config.user_state_path
        if state_path.exists():
            zf.write(state_path, "app_state.json")

    def _add_logs(self, zf: zipfile.ZipFile):
        log_dir = Path("logs")
        if log_dir.exists():
            for log_file in log_dir.glob("*.log"):
                try:
                    zf.write(log_file, f"logs/{log_file.name}")
                except Exception:
                    pass


diagnostics_service = DiagnosticsService()
