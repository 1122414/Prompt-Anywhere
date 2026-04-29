import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

_DEFAULTS: Dict[str, Any] = {
    "storage": {
        "data_dir": "./data",
        "export_dir": "./exports",
        "backup_dir": "./backups",
        "log_dir": "./logs",
    },
    "behavior": {
        "hotkey": "ctrl+alt+p",
        "main_hotkey": "ctrl+alt+m",
        "copy_auto_hide": True,
        "start_minimized": False,
        "start_with_windows": False,
        "close_to_tray": True,
    },
    "window": {
        "always_on_top": True,
        "opacity": 1.0,
        "default_width": 900,
        "default_height": 600,
        "remember_position": True,
        "remember_size": True,
    },
    "backup": {
        "auto_backup_enabled": True,
        "auto_backup_interval_hours": 24,
        "max_backup_count": 20,
    },
    "history": {
        "enabled": True,
        "max_versions_per_file": 20,
    },
    "features": {
        "template_variables": True,
        "composer": True,
        "builtin_templates": True,
        "clipboard_collector": False,
    },
}


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _get_nested(data: Dict[str, Any], dotted_key: str, default: Any = None) -> Any:
    parts = dotted_key.split(".")
    current: Any = data
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return default
    return current


def _set_nested(data: Dict[str, Any], dotted_key: str, value: Any) -> None:
    parts = dotted_key.split(".")
    current = data
    for part in parts[:-1]:
        if part not in current or not isinstance(current[part], dict):
            current[part] = {}
        current = current[part]
    current[parts[-1]] = value


class ConfigService:
    _instance: "ConfigService | None" = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._env_defaults = {}
            cls._instance._user_config = {}
            cls._instance._config_path = Path("app_config.json")
            cls._instance._load_env_defaults()
            cls._instance._load_user_config()
        return cls._instance

    def _load_env_defaults(self):
        load_dotenv(override=False)
        env_mapping = {
            "DATA_DIR": ("storage", "data_dir"),
            "EXPORT_DIR": ("storage", "export_dir"),
            "DEFAULT_BACKUP_DIR": ("storage", "backup_dir"),
            "DEFAULT_LOG_DIR": ("storage", "log_dir"),
            "GLOBAL_HOTKEY": ("behavior", "hotkey"),
            "DEFAULT_MAIN_HOTKEY": ("behavior", "main_hotkey"),
            "COPY_AUTO_HIDE": ("behavior", "copy_auto_hide"),
            "START_MINIMIZED": ("behavior", "start_minimized"),
            "ALWAYS_ON_TOP": ("window", "always_on_top"),
            "DEFAULT_WINDOW_OPACITY": ("window", "opacity"),
            "DEFAULT_WINDOW_WIDTH": ("window", "default_width"),
            "DEFAULT_WINDOW_HEIGHT": ("window", "default_height"),
            "APP_CONFIG_PATH": None,
        }
        self._env_defaults = {}
        for env_key, path in env_mapping.items():
            raw = os.getenv(env_key)
            if raw is not None and raw != "":
                value = raw
                if raw.lower() in ("true", "1", "yes"):
                    value = True
                elif raw.lower() in ("false", "0", "no"):
                    value = False
                else:
                    try:
                        value = int(raw)
                    except ValueError:
                        try:
                            value = float(raw)
                        except ValueError:
                            pass
                if path is not None:
                    _set_nested(self._env_defaults, ".".join(path), value)
                elif env_key == "APP_CONFIG_PATH":
                    self._config_path = Path(raw)
        self._config_path = self._config_path.resolve()

    def _load_user_config(self):
        if self._config_path.exists():
            try:
                with open(self._config_path, "r", encoding="utf-8") as f:
                    self._user_config = json.load(f)
                if not isinstance(self._user_config, dict):
                    logger.warning("app_config.json root is not a dict, using defaults")
                    self._user_config = {}
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Failed to load app_config.json: {e}")
                self._user_config = {}
        else:
            self._user_config = {}
            self.save_user_config()

    def get(self, key: str, default=None):
        value = _get_nested(self._user_config, key)
        if value is not None:
            return value
        value = _get_nested(self._env_defaults, key)
        if value is not None:
            return value
        value = _get_nested(_DEFAULTS, key)
        if value is not None:
            return value
        return default

    def set(self, key: str, value):
        _set_nested(self._user_config, key, value)
        self.save_user_config()

    def save_user_config(self):
        try:
            self._config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(self._user_config, f, ensure_ascii=False, indent=2)
        except OSError as e:
            logger.warning(f"Failed to save app_config.json: {e}")

    def reset_to_defaults(self):
        self._user_config = {}
        self.save_user_config()
        self._load_env_defaults()

    def get_all(self) -> Dict[str, Any]:
        merged = _deep_merge(_DEFAULTS, self._env_defaults)
        merged = _deep_merge(merged, self._user_config)
        return merged


config_service = ConfigService()
