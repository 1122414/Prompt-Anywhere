import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Set

import yaml
from dotenv import load_dotenv


def _base_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent.parent


load_dotenv(_base_path() / ".env")

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
    "SEARCH_ENABLE_PINYIN": ["search", "enable_pinyin"],
    "SEARCH_ENABLE_INITIALS": ["search", "enable_initials"],
    "SEARCH_ENABLE_FUZZY": ["search", "enable_fuzzy"],
    "SEARCH_FUZZY_THRESHOLD": ["search", "fuzzy_threshold"],
    "SEARCH_FUZZY_MODE": ["search", "fuzzy_mode"],
    "SEARCH_FIRST_PAINT_RESULTS": ["search", "first_paint_results"],
    "SEMANTIC_SEARCH_ENABLED": ["semantic_search", "enabled"],
    "SEMANTIC_SEARCH_PROVIDER": ["semantic_search", "provider"],
    "SEMANTIC_SEARCH_LOCAL_MODEL": ["semantic_search", "local_model"],
    "SEMANTIC_SEARCH_API_BASE_URL": ["semantic_search", "api_base_url"],
    "SEMANTIC_SEARCH_API_KEY": ["semantic_search", "api_key"],
    "SEMANTIC_SEARCH_API_MODEL": ["semantic_search", "api_model"],
    "SEMANTIC_SEARCH_TOP_K": ["semantic_search", "top_k"],
    "SEMANTIC_SEARCH_MIN_SCORE": ["semantic_search", "min_score"],
    "SEMANTIC_SEARCH_INDEX_ON_STARTUP": ["semantic_search", "index_on_startup"],
    "SEMANTIC_SEARCH_AUTO_REINDEX": ["semantic_search", "auto_reindex"],
    "KNOWLEDGE_BASE_DIR": ["knowledge_base", "dir"],
    "KNOWLEDGE_BASE_AUTO_SYNC": ["knowledge_base", "auto_sync"],
    "AI_TEMPLATE_ENABLED": ["ai_template", "enabled"],
    "AI_TEMPLATE_PROVIDER": ["ai_template", "provider"],
    "AI_TEMPLATE_BASE_URL": ["ai_template", "base_url"],
    "AI_TEMPLATE_API_KEY": ["ai_template", "api_key"],
    "AI_TEMPLATE_MODEL": ["ai_template", "model"],
    "AI_TEMPLATE_TEMPERATURE": ["ai_template", "temperature"],
    "AI_TEMPLATE_TIMEOUT_SECONDS": ["ai_template", "timeout_seconds"],
    "AI_TEMPLATE_DETECTION_MODE": ["ai_template", "detection_mode"],
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
    "TEMPLATE_VARIABLE_PATTERN": ["template", "variable_pattern"],
    "TEMPLATE_VARIABLE_MAX_COUNT": ["template", "variable_max_count"],
    "TEMPLATE_DEFAULT_MULTILINE": ["template", "default_multiline"],
    "COMPOSER_SEPARATOR": ["composer", "separator"],
    "COMPOSER_INCLUDE_FILE_TITLE": ["composer", "include_file_title"],
    "COMPOSER_TITLE_LEVEL": ["composer", "title_level"],
    "COMPOSER_AUTO_DETECT_VARIABLES": ["composer", "auto_detect_variables"],
    "COMPOSER_SAVE_DIR": ["composer", "save_dir"],
    "COMPOSER_EXPORT_DIR": ["composer", "export_dir"],
    "SHOW_TEMPLATE_BUTTON": ["ui", "show_template_button"],
    "SHOW_COMPOSER_BUTTON": ["ui", "show_composer_button"],
    "COMPOSER_WINDOW_WIDTH": ["ui", "composer_window_width"],
    "COMPOSER_WINDOW_HEIGHT": ["ui", "composer_window_height"],
    "TEMPLATE_DIALOG_WIDTH": ["ui", "template_dialog_width"],
    "TEMPLATE_DIALOG_HEIGHT": ["ui", "template_dialog_height"],
    "BUILTIN_TEMPLATE_DIR": ["builtin_templates", "dir"],
    "ENABLE_BUILTIN_TEMPLATES": ["builtin_templates", "enabled"],
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
        config_path = _base_path() / "config.yaml"
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

    def _get_pref(self, key: str, default: Any = None) -> Any:
        try:
            from app.services.state_service import state_service
            pref = state_service.get_preference(key, None)
            if pref is not None:
                return pref
        except Exception:
            pass
        return default

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

    @property
    def search_enable_pinyin(self) -> bool:
        return self._get_env("SEARCH_ENABLE_PINYIN", True)

    @property
    def search_enable_initials(self) -> bool:
        return self._get_env("SEARCH_ENABLE_INITIALS", True)

    @property
    def search_enable_fuzzy(self) -> bool:
        return self._get_env("SEARCH_ENABLE_FUZZY", True)

    @property
    def search_fuzzy_threshold(self) -> int:
        return int(self._get_env("SEARCH_FUZZY_THRESHOLD", "60"))

    @property
    def search_fuzzy_mode(self) -> str:
        return self._get_env("SEARCH_FUZZY_MODE", "balanced")

    @property
    def search_first_paint_results(self) -> int:
        return int(self._get_env("SEARCH_FIRST_PAINT_RESULTS", "30"))

    # ============ 语义搜索配置 ============
    @property
    def semantic_search_enabled(self) -> bool:
        return self._get_env("SEMANTIC_SEARCH_ENABLED", False)

    @property
    def semantic_search_provider(self) -> str:
        return self._get_env("SEMANTIC_SEARCH_PROVIDER", "api")

    @property
    def semantic_search_local_model(self) -> str:
        return self._get_env("SEMANTIC_SEARCH_LOCAL_MODEL", "BAAI/bge-small-zh-v1.5")

    @property
    def semantic_search_api_base_url(self) -> str:
        return self._get_env("SEMANTIC_SEARCH_API_BASE_URL", "")

    @property
    def semantic_search_api_key(self) -> str:
        return self._get_env("SEMANTIC_SEARCH_API_KEY", "")

    @property
    def semantic_search_api_model(self) -> str:
        return self._get_env("SEMANTIC_SEARCH_API_MODEL", "text-embedding-3-small")

    @property
    def semantic_search_top_k(self) -> int:
        return int(self._get_env("SEMANTIC_SEARCH_TOP_K", "20"))

    @property
    def semantic_search_min_score(self) -> float:
        return float(self._get_env("SEMANTIC_SEARCH_MIN_SCORE", "0.35"))

    @property
    def semantic_search_index_on_startup(self) -> bool:
        return self._get_env("SEMANTIC_SEARCH_INDEX_ON_STARTUP", False)

    @property
    def semantic_search_auto_reindex(self) -> bool:
        return self._get_env("SEMANTIC_SEARCH_AUTO_REINDEX", True)

    # ============ 知识库配置 ============
    @property
    def knowledge_base_dir(self) -> Path:
        path = self._get_env("KNOWLEDGE_BASE_DIR", "./.prompt_anywhere")
        return self.data_dir / path

    @property
    def knowledge_base_auto_sync(self) -> bool:
        return self._get_env("KNOWLEDGE_BASE_AUTO_SYNC", True)

    # ============ AI模板助手配置 ============
    @property
    def ai_template_enabled(self) -> bool:
        return self._get_env("AI_TEMPLATE_ENABLED", False)

    @property
    def ai_template_provider(self) -> str:
        return self._get_env("AI_TEMPLATE_PROVIDER", "openai_compatible")

    @property
    def ai_template_base_url(self) -> str:
        return self._get_env("AI_TEMPLATE_BASE_URL", "")

    @property
    def ai_template_api_key(self) -> str:
        return self._get_env("AI_TEMPLATE_API_KEY", "")

    @property
    def ai_template_model(self) -> str:
        return self._get_env("AI_TEMPLATE_MODEL", "")

    @property
    def ai_template_temperature(self) -> float:
        return float(self._get_env("AI_TEMPLATE_TEMPERATURE", "0.2"))

    @property
    def ai_template_timeout_seconds(self) -> int:
        return int(self._get_env("AI_TEMPLATE_TIMEOUT_SECONDS", "30"))

    @property
    def ai_template_detection_mode(self) -> str:
        return self._get_env("AI_TEMPLATE_DETECTION_MODE", "hybrid")

    # ============ 复制配置 ============
    # ============ Esc 配置 ============
    @property
    def search_selected_bg_color(self) -> str:
        return self._get_pref("search_selected_bg_color", self._get_env("SEARCH_SELECTED_BG_COLOR", "#e3f2fd"))

    @property
    def copy_auto_hide(self) -> bool:
        return self._get_pref("copy_auto_hide", self._get_env("COPY_AUTO_HIDE", True))

    @property
    def copy_hide_delay_ms(self) -> int:
        return int(self._get_pref("copy_hide_delay_ms", int(self._get_env("COPY_HIDE_DELAY_MS", "200"))))

    @property
    def esc_hide_enabled(self) -> bool:
        return self._get_pref("esc_hide_enabled", self._get_env("ESC_HIDE_ENABLED", True))

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

    # ============ 模板变量配置 ============
    @property
    def template_variable_pattern(self) -> str:
        return self._get_env("TEMPLATE_VARIABLE_PATTERN", r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")

    @property
    def template_variable_max_count(self) -> int:
        return int(self._get_env("TEMPLATE_VARIABLE_MAX_COUNT", "50"))

    @property
    def template_default_multiline(self) -> bool:
        return self._get_env("TEMPLATE_DEFAULT_MULTILINE", True)

    # ============ Composer 配置 ============
    @property
    def composer_separator(self) -> str:
        raw = self._get_env("COMPOSER_SEPARATOR", "\n\n---\n\n")
        return raw.replace("\\n", "\n").replace("\\t", "\t")

    @property
    def composer_include_file_title(self) -> bool:
        return self._get_env("COMPOSER_INCLUDE_FILE_TITLE", True)

    @property
    def composer_title_level(self) -> int:
        return int(self._get_env("COMPOSER_TITLE_LEVEL", "1"))

    @property
    def composer_auto_detect_variables(self) -> bool:
        return self._get_env("COMPOSER_AUTO_DETECT_VARIABLES", True)

    @property
    def composer_save_dir(self) -> Path:
        path = self._get_env("COMPOSER_SAVE_DIR", "./data/组合模板")
        return Path(path).resolve()

    @property
    def composer_export_dir(self) -> Path:
        path = self._get_env("COMPOSER_EXPORT_DIR", "./exports")
        return Path(path).resolve()

    # ============ UI 按钮显示配置 ============
    @property
    def show_template_button(self) -> bool:
        return self._get_pref("show_template_button", self._get_env("SHOW_TEMPLATE_BUTTON", True))

    @property
    def show_composer_button(self) -> bool:
        return self._get_pref("show_composer_button", self._get_env("SHOW_COMPOSER_BUTTON", True))

    @property
    def composer_window_width(self) -> int:
        return int(self._get_env("COMPOSER_WINDOW_WIDTH", "900"))

    @property
    def composer_window_height(self) -> int:
        return int(self._get_env("COMPOSER_WINDOW_HEIGHT", "600"))

    @property
    def template_dialog_width(self) -> int:
        return int(self._get_env("TEMPLATE_DIALOG_WIDTH", "700"))

    @property
    def template_dialog_height(self) -> int:
        return int(self._get_env("TEMPLATE_DIALOG_HEIGHT", "520"))

    # ============ 内置模板配置 ============
    @property
    def builtin_template_dir(self) -> Path:
        if getattr(sys, "frozen", False):
            return Path(sys._MEIPASS) / "builtin_templates"
        path = self._get_env("BUILTIN_TEMPLATE_DIR", "./builtin_templates")
        return Path(path).resolve()

    @property
    def enable_builtin_templates(self) -> bool:
        return self._get_pref("enable_builtin_templates", self._get_env("ENABLE_BUILTIN_TEMPLATES", True))

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
        config_path = _base_path() / "config.yaml"
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
        config_path = _base_path() / "config.yaml"
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(self._config_data, f, allow_unicode=True, sort_keys=False)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to save config: {e}")


config = Config()
