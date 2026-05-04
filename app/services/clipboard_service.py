from PySide6.QtWidgets import QApplication

from app.utils.singleton import Singleton


class ClipboardService(Singleton):
    _instance = None

    def copy_text(self, text: str) -> bool:
        try:
            app = QApplication.instance()
            if app is None:
                return False
            clipboard = app.clipboard()
            clipboard.setText(text)
            return True
        except Exception:
            return False


clipboard_service = ClipboardService()
