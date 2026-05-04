from app.utils.singleton import Singleton


class NotificationService(Singleton):

    def _init(self):
        self._toasts = []

    def success(self, parent, message: str, duration_ms: int = 1600):
        from app.ui.toast import Toast
        toast = Toast(parent, message, duration_ms, "success")
        toast.show_at_parent()

    def warning(self, parent, message: str, duration_ms: int = 2200):
        from app.ui.toast import Toast
        toast = Toast(parent, message, duration_ms, "warning")
        toast.show_at_parent()

    def error(self, parent, message: str, duration_ms: int = 2600):
        from app.ui.toast import Toast
        toast = Toast(parent, message, duration_ms, "error")
        toast.show_at_parent()


notification_service = NotificationService()
