from PySide6.QtCore import QPropertyAnimation, QTimer, Qt, QPoint
from PySide6.QtWidgets import QLabel, QWidget


class Toast(QWidget):
    _active_toasts = []

    def __init__(self, parent, message: str, duration_ms: int = 1600, style: str = "success"):
        super().__init__(parent)
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        colors = {
            "success": ("#4CAF50", "#fff"),
            "warning": ("#FF9800", "#fff"),
            "error": ("#F44336", "#fff"),
        }
        bg, fg = colors.get(style, colors["success"])

        self.label = QLabel(message, self)
        self.label.setStyleSheet(
            f"QLabel {{ background: {bg}; color: {fg}; padding: 8px 20px; "
            f"border-radius: 6px; font-size: 13px; }}"
        )
        self.label.adjustSize()
        self.resize(self.label.sizeHint())

        self._fade_timer = QTimer(self)
        self._fade_timer.setSingleShot(True)
        self._fade_timer.timeout.connect(self._fade_out)
        self._fade_timer.start(duration_ms)

        while Toast._active_toasts:
            old = Toast._active_toasts.pop()
            old.close()
        Toast._active_toasts.append(self)

    def show_at_parent(self):
        if self.parent():
            parent_rect = self.parent().rect()
            x = self.parent().x() + (parent_rect.width() - self.width()) // 2
            y = self.parent().y() + parent_rect.height() - 100
            self.move(x, y)
        self.setWindowOpacity(0.95)
        self.show()

    def _fade_out(self):
        self._animation = QPropertyAnimation(self, b"windowOpacity")
        self._animation.setDuration(300)
        self._animation.setStartValue(0.95)
        self._animation.setEndValue(0.0)
        self._animation.finished.connect(self.close)
        self._animation.start()
