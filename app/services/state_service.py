import json
import logging
from typing import Any, Dict

from app.config import config
from app.utils.json_store import JsonFileStore
from app.utils.singleton import Singleton

logger = logging.getLogger(__name__)


class StateService(Singleton):

    def _init(self):
        self._state: Dict[str, Any] = {}
        self._load_state()

    def _load_state(self):
        state_path = config.user_state_path
        data = JsonFileStore.load(state_path, {})
        self._state = data if isinstance(data, dict) else {}

    def _save_state(self):
        JsonFileStore.save(config.user_state_path, self._state)

    def get_window_state(self) -> Dict[str, Any]:
        return self._state.get("window", {})

    def set_window_state(self, x: int, y: int, width: int, height: int, opacity: float, always_on_top: bool):
        if "window" not in self._state:
            self._state["window"] = {}
        self._state["window"]["x"] = x
        self._state["window"]["y"] = y
        self._state["window"]["width"] = width
        self._state["window"]["height"] = height
        self._state["window"]["opacity"] = opacity
        self._state["window"]["always_on_top"] = always_on_top
        self._save_state()

    def get_last_selected_category(self) -> str:
        return self._state.get("last_selected_category", "")

    def set_last_selected_category(self, category: str):
        self._state["last_selected_category"] = category
        self._save_state()

    def get_last_selected_file(self) -> str:
        return self._state.get("last_selected_file", "")

    def set_last_selected_file(self, file_path: str):
        self._state["last_selected_file"] = file_path
        self._save_state()

    def get_last_view_mode(self) -> str:
        return self._state.get("last_view_mode", config.default_view_mode)

    def set_last_view_mode(self, mode: str):
        self._state["last_view_mode"] = mode
        self._save_state()

    def get_favorites(self) -> list:
        return self._state.get("favorites", [])

    def set_favorites(self, favorites: list):
        self._state["favorites"] = favorites
        self._save_state()

    def add_favorite(self, file_path: str):
        favorites = self.get_favorites()
        if file_path not in favorites:
            favorites.append(file_path)
            self.set_favorites(favorites)

    def remove_favorite(self, file_path: str):
        favorites = self.get_favorites()
        if file_path in favorites:
            favorites.remove(file_path)
            self.set_favorites(favorites)

    def is_favorite(self, file_path: str) -> bool:
        return file_path in self.get_favorites()

    def get_recent_files(self) -> list:
        return self._state.get("recent_files", [])

    def set_recent_files(self, recent_files: list):
        self._state["recent_files"] = recent_files
        self._save_state()

    def add_recent_file(self, file_path: str):
        from datetime import datetime
        recent = self.get_recent_files()
        existing = None
        for r in recent:
            if r.get("path") == file_path:
                existing = r
                break
        if existing:
            recent.remove(existing)
            use_count = existing.get("use_count", 0) + 1
        else:
            use_count = 1
        recent.insert(0, {
            "path": file_path,
            "last_used_at": datetime.now().isoformat(),
            "use_count": use_count,
        })
        recent = recent[:config.max_recent_files]
        self.set_recent_files(recent)

    def get_folder_order(self, folder_path: str) -> list:
        return self._state.get("folder_orders", {}).get(folder_path, [])

    def set_folder_order(self, folder_path: str, file_names: list):
        if "folder_orders" not in self._state:
            self._state["folder_orders"] = {}
        self._state["folder_orders"][folder_path] = file_names
        self._save_state()

    def get_preference(self, key: str, default=None):
        return self._state.get("preferences", {}).get(key, default)

    def set_preference(self, key: str, value):
        if "preferences" not in self._state:
            self._state["preferences"] = {}
        self._state["preferences"][key] = value
        self._save_state()

    def get_all_preferences(self) -> dict:
        return self._state.get("preferences", {})

    def reset_all_preferences(self):
        self._state.pop("preferences", None)
        self._save_state()


state_service = StateService()
