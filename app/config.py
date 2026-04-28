import os
from pathlib import Path
from typing import Any, Dict, List, Set

import yaml
from dotenv import load_dotenv

load_dotenv()

_ENV_TO_YAML_PATH: Dict[str, List[str]] = {
    "APP_NAME": ["app", "name"],
    "APP_VERSION": ["app", "version"],
    "GLOBAL_HOTKEY": ["app", "hotkey"],
    "QUICK_MODE_HOTKEY": ["app", "quick_mode_hotkey"],
    "ALWAYS_ON_TOP": ["app", "always_on_top"],
    "START_MINIMIZED": ["app", "start_minimized"],
    "ESC_HIDE_ENABLED": ["app", "esc_hide_enabled"],
    "COPY_AUTO_HIDE": ["app", "copy_auto_hide"],
    "COPY_HIDE_DELAY_MS": ["app", "copy_hide_delay_ms"],
    "DATA_DIR": ["storage", "data_dir"],
    "EXPORT_DIR": ["storage", "export_dir"],
    "USER_STATE_PATH": ["storage", "user_state_path"],
    "FILE_ENCODING": ["storage", "file_encoding"],
    "DEFAULT_WINDOW_WIDTH": ["ui", "default_window_width"],
    "DEFAULT_WINDOW_HEIGHT": ["ui", "default_window_height"],
    "DEFAULT_WINDOW_OPACITY": ["ui", "default_window_opacity"],
    "MIN_WINDOW_OPACITY": ["ui", "min_window_opacity"],
    "MAX_WINDOW_OPACITY": ["ui", "max_window_opacity"],
    "DEFAULT_VIEW_MODE": ["ui", "default_view_mode"],
    "PYGMENTS_STYLE": ["ui", "pygments_style"],
    "SEARCH_DEBOUNCE_MS": ["search", "debounce_ms"],
    "SEARCH_MAX_RESULTS": ["search", "max_results"],
    "SEARCH_SNIPPET_RADIUS": ["search", "snippet_radius"],
    "SEARCH_HIGHLIGHT_ENABLED": ["search", "highlight_enabled"],
    "SEARCH_CASE_INSENSITIVE": ["search", "case_insensitive"],
    "SUPPORTED_PROMPT_EXTENSIONS": ["file", "supported_extensions"],
    "IMAGE_ASSETS_DIR_NAME": ["file", "image_assets_dir_name"],
    "PASTED_IMAGE_FORMAT": ["file", "pasted_image_format"],
    "LOG_LEVEL": ["app", "log_level"],
    "ENABLE_FILE_WATCHER": ["app", "enable_file_watcher"],
    "MODEL_PROVIDER": ["model", "provider"],
    "MODEL_NAME": ["model", "name"],
    "MODEL_API_KEY": ["model", "api_key"],
    "MODEL_BASE_URL": ["model", "base_url"],
    "MODEL_TEMPERATURE": ["model", "temperature"],
    "FOLDER_ICONS": ["ui", "folder_icons"],
}


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
        if env_value is not None and env_value != "":
            if env_value.lower() in ("true", "1", "yes"):
                return True
            if env_value.lower() in ("false", "0", "no"):
                return False
            return env_value

        path = _ENV_TO_YAML_PATH.get(key, [])
        value = self._config_data
        for k in path:
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
    def app_env(self) -> str:
        return self._get_env("APP_ENV", "local")

    # ============ 热键配置 ============
    @property
    def hotkey(self) -> str:
        return self._get_env("GLOBAL_HOTKEY", "ctrl+alt+p")

    @property
    def quick_mode_hotkey(self) -> str:
        return self._get_env("QUICK_MODE_HOTKEY", "ctrl+alt+p")

    # ============ 窗口配置 ============
    @property
    def always_on_top(self) -> bool:
        return self._get_env("ALWAYS_ON_TOP", True)

    @property
    def start_minimized(self) -> bool:
        return self._get_env("START_MINIMIZED", False)

    @property
    def default_window_width(self) -> int:
        return int(self._get_env("DEFAULT_WINDOW_WIDTH", 900))

    @property
    def default_window_height(self) -> int:
        return int(self._get_env("DEFAULT_WINDOW_HEIGHT", 600))

    @property
    def default_window_opacity(self) -> float:
        return float(self._get_env("DEFAULT_WINDOW_OPACITY", "1.0"))

    @property
    def min_window_opacity(self) -> float:
        return float(self._get_env("MIN_WINDOW_OPACITY", "0.60"))

    @property
    def max_window_opacity(self) -> float:
        return float(self._get_env("MAX_WINDOW_OPACITY", "1.00"))

    # ============ 存储配置 ============
    @property
    def data_dir(self) -> Path:
        path = self._get_env("DATA_DIR", "./data")
        return Path(path).resolve()

    @property
    def export_dir(self) -> Path:
        path = self._get_env("EXPORT_DIR", "./exports")
        return Path(path).resolve()

    @property
    def user_state_path(self) -> Path:
        path = self._get_env("USER_STATE_PATH", "./app_state.json")
        return Path(path).resolve()

    @property
    def file_encoding(self) -> str:
        return self._get_env("FILE_ENCODING", "utf-8")

    # ============ UI 配置 ============
    @property
    def default_view_mode(self) -> str:
        return self._get_env("DEFAULT_VIEW_MODE", "edit")

    @property
    def pygments_style(self) -> str:
        return self._get_env("PYGMENTS_STYLE", "github-dark")

    # ============ 搜索配置 ============
    @property
    def search_debounce_ms(self) -> int:
        return int(self._get_env("SEARCH_DEBOUNCE_MS", "180"))

    @property
    def search_max_results(self) -> int:
        return int(self._get_env("SEARCH_MAX_RESULTS", "100"))

    @property
    def search_snippet_radius(self) -> int:
        return int(self._get_env("SEARCH_SNIPPET_RADIUS", "40"))

    @property
    def search_highlight_enabled(self) -> bool:
        return self._get_env("SEARCH_HIGHLIGHT_ENABLED", True)

    @property
    def search_case_insensitive(self) -> bool:
        return self._get_env("SEARCH_CASE_INSENSITIVE", True)

    # ============ 复制配置 ============
    @property
    def copy_auto_hide(self) -> bool:
        return self._get_env("COPY_AUTO_HIDE", True)

    @property
    def copy_hide_delay_ms(self) -> int:
        return int(self._get_env("COPY_HIDE_DELAY_MS", "200"))

    # ============ Esc 配置 ============
    @property
    def esc_hide_enabled(self) -> bool:
        return self._get_env("ESC_HIDE_ENABLED", True)

    # ============ 文件类型配置 ============
    @property
    def supported_prompt_extensions(self) -> Set[str]:
        ext_str = self._get_env("SUPPORTED_PROMPT_EXTENSIONS", ".md,.txt")
        return set(ext.strip().lower() for ext in ext_str.split(",") if ext.strip())

    @property
    def image_assets_dir_name(self) -> str:
        return self._get_env("IMAGE_ASSETS_DIR_NAME", "_assets")

    @property
    def pasted_image_format(self) -> str:
        return self._get_env("PASTED_IMAGE_FORMAT", "png")

    # ============ 调试配置 ============
    @property
    def log_level(self) -> str:
        return self._get_env("LOG_LEVEL", "INFO")

    @property
    def max_recent_files(self) -> int:
        val = int(self._get_env("MAX_RECENT_FILES", "10"))
        return max(1, min(val, 20))

    @property
    def enable_file_watcher(self) -> bool:
        return self._get_env("ENABLE_FILE_WATCHER", True)

    # ============ 模型配置（预留） ============
    @property
    def model_provider(self) -> str:
        return self._get_env("MODEL_PROVIDER", "")

    @property
    def model_name(self) -> str:
        return self._get_env("MODEL_NAME", "")

    @property
    def model_api_key(self) -> str:
        return self._get_env("MODEL_API_KEY", "")

    @property
    def model_base_url(self) -> str:
        return self._get_env("MODEL_BASE_URL", "")

    @property
    def model_temperature(self) -> float:
        return float(self._get_env("MODEL_TEMPERATURE", "0.7"))

    # ============ 文件夹图标配置 ============
    def folder_icon(self, folder_path: str) -> str:
        icons = self._config_data.get("ui", {}).get("folder_icons", {})
        return icons.get(folder_path, "")

    def set_folder_icon(self, folder_path: str, icon_key: str) -> None:
        if "ui" not in self._config_data:
            self._config_data["ui"] = {}
        if "folder_icons" not in self._config_data["ui"]:
            self._config_data["ui"]["folder_icons"] = {}
        self._config_data["ui"]["folder_icons"][folder_path] = icon_key
        config_path = Path(__file__).parent.parent / "config.yaml"
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(self._config_data, f, allow_unicode=True, sort_keys=False)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to save config: {e}")

    def rename_folder_icons(self, old_path: str, new_path: str) -> None:
        icons = self._config_data.get("ui", {}).get("folder_icons", {})
        if not icons:
            return
        updated = {}
        for key, value in icons.items():
            if key == old_path or key.startswith(old_path + "/"):
                new_key = new_path + key[len(old_path):]
                updated[new_key] = value
            else:
                updated[key] = value
        self._config_data["ui"]["folder_icons"] = updated
        config_path = Path(__file__).parent.parent / "config.yaml"
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(self._config_data, f, allow_unicode=True, sort_keys=False)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to save config: {e}")


config = Config()
