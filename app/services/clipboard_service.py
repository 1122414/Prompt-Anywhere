from PySide6.QtWidgets import QApplication


class ClipboardService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

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
