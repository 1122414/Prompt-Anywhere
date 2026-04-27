from PySide6.QtCore import Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from app.config import config
from app.constants import AppConstants


class TrayManager(QSystemTrayIcon):
    toggle_window = Signal()
    new_prompt = Signal()
    open_data_dir = Signal()
    quit_app = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setToolTip(AppConstants.APP_NAME)
        self._setup_menu()
        self.activated.connect(self._on_activated)

    def _setup_menu(self):
        self.menu = QMenu()

        self.toggle_action = QAction("显示 / 隐藏", self.menu)
        self.toggle_action.triggered.connect(self.toggle_window.emit)
        self.menu.addAction(self.toggle_action)

        self.menu.addSeparator()

        self.new_action = QAction("新建提示词", self.menu)
        self.new_action.triggered.connect(self.new_prompt.emit)
        self.menu.addAction(self.new_action)

        self.open_dir_action = QAction("打开数据目录", self.menu)
        self.open_dir_action.triggered.connect(self.open_data_dir.emit)
        self.menu.addAction(self.open_dir_action)

        self.menu.addSeparator()

        self.quit_action = QAction("退出", self.menu)
        self.quit_action.triggered.connect(self.quit_app.emit)
        self.menu.addAction(self.quit_action)

        self.setContextMenu(self.menu)

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.toggle_window.emit()
