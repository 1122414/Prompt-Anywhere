import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from app.config import config

logger = logging.getLogger(__name__)


class StateService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._state: Dict[str, Any] = {}
            cls._instance._load_state()
        return cls._instance

    def _load_state(self):
        state_path = config.user_state_path
        if state_path.exists():
            try:
                with open(state_path, "r", encoding="utf-8") as f:
                    self._state = json.load(f) or {}
            except Exception as e:
                logger.warning(f"Failed to load state: {e}")
                self._state = {}

    def _save_state(self):
        state_path = config.user_state_path
        try:
            state_path.parent.mkdir(parents=True, exist_ok=True)
            with open(state_path, "w", encoding="utf-8") as f:
                json.dump(self._state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save state: {e}")

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


state_service = StateService()
