import os
from pathlib import Path
from typing import Any, Dict

import yaml
from dotenv import load_dotenv

load_dotenv()


class Config:
    _instance = None
    _config_data: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self) -> None:
        config_path = Path(__file__).parent.parent / "config.yaml"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                self._config_data = yaml.safe_load(f) or {}

    def _get_env(self, key: str, default: Any = None) -> Any:
        env_value = os.getenv(key)
        if env_value is not None:
            if env_value.lower() in ("true", "1", "yes"):
                return True
            if env_value.lower() in ("false", "0", "no"):
                return False
            return env_value

        keys = key.lower().split("_")
        value = self._config_data
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value if value is not None else default

    @property
    def app_name(self) -> str:
        return self._get_env("APP_NAME", "Prompt Anywhere")

    @property
    def app_version(self) -> str:
        return self._get_env("APP_VERSION", "0.1.0")

    @property
    def hotkey(self) -> str:
        return self._get_env("GLOBAL_HOTKEY", "ctrl+alt+p")

    @property
    def always_on_top(self) -> bool:
        return self._get_env("ALWAYS_ON_TOP", True)

    @property
    def start_minimized(self) -> bool:
        return self._get_env("START_MINIMIZED", False)

    @property
    def data_dir(self) -> Path:
        path = self._get_env("DATA_DIR", "./data")
        return Path(path).resolve()

    @property
    def export_dir(self) -> Path:
        path = self._get_env("EXPORT_DIR", "./exports")
        return Path(path).resolve()

    @property
    def window_x(self) -> int:
        return int(self._get_env("WINDOW_X", 100))

    @property
    def window_y(self) -> int:
        return int(self._get_env("WINDOW_Y", 100))

    @property
    def window_width(self) -> int:
        return int(self._get_env("WINDOW_WIDTH", 900))

    @property
    def window_height(self) -> int:
        return int(self._get_env("WINDOW_HEIGHT", 600))

    @property
    def default_mode(self) -> str:
        return self._get_env("DEFAULT_MODE", "edit")

    @property
    def file_encoding(self) -> str:
        return self._get_env("FILE_ENCODING", "utf-8")

    @property
    def pygments_style(self) -> str:
        return self._get_env("PYGMENTS_STYLE", "github-dark")

    @property
    def search_case_insensitive(self) -> bool:
        return self._get_env("SEARCH_CASE_INSENSITIVE", True)

    @property
    def log_level(self) -> str:
        return self._get_env("LOG_LEVEL", "INFO")

    @property
    def enable_file_watcher(self) -> bool:
        return self._get_env("ENABLE_FILE_WATCHER", True)


config = Config()
