from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QLabel,
    QLineEdit,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

from app.config import config
from app.constants import Messages
from app.services.clipboard_service import clipboard_service
from app.services.file_service import PromptFile
from app.services.search_service import SearchResult
from app.services.state_service import state_service
from app.services.usage_service import usage_service
from app.services.notification_service import notification_service
from app.ui.search_mixin import SearchMixin
from app.ui.search_result_panel import SearchResultPanel


class QuickWindow(QMainWindow, SearchMixin):
    open_main_requested = Signal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{config.app_name} - 快速模式")
        from app.utils.icon_utils import create_app_icon
        self.setWindowIcon(create_app_icon())
        self.setMinimumSize(500, 400)
        self.resize(600, 450)

        self._setup_search()
        self._setup_ui()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(Messages.SEARCH_PLACEHOLDER)
        self.search_input.textChanged.connect(self._on_search_input)
        self.search_input.installEventFilter(self)
        layout.addWidget(self.search_input)

        self.search_result_panel = SearchResultPanel()
        self.search_result_panel.result_selected.connect(self._on_result_selected)
        self.search_result_panel.result_copy_requested.connect(self._on_result_copy)
        self.search_result_panel.escape_pressed.connect(self._on_escape)
        layout.addWidget(self.search_result_panel)

        hint = QLabel("↑↓ 选择  |  Enter 复制并关闭  |  Shift+Enter 复制  |  Esc 关闭")
        hint.setStyleSheet("color: #888; font-size: 11px; padding: 4px;")
        layout.addWidget(hint)

    def showEvent(self, event):
        super().showEvent(event)
        self.search_input.setFocus()
        self.search_input.selectAll()

    def toggle_visibility(self):
        if self.isVisible() and not self.isMinimized():
            self.hide()
        else:
            self.setWindowFlags(
                self.windowFlags()
                | Qt.WindowStaysOnTopHint
                | Qt.Tool
            )
            self.showNormal()
            self.activateWindow()
            self.raise_()
            self.search_input.setFocus()
            self.search_input.selectAll()

    def _clear_search_results(self):
        self.search_result_panel.clear_results()

    def _display_search_results(self, results, keyword):
        self.search_result_panel.set_results(results, keyword)
        if self.search_result_panel.result_list.count() > 0:
            self.search_result_panel.select_first()

    def _on_result_selected(self, result: SearchResult):
        self._copy_result(result)

    def _on_result_copy(self, result: SearchResult):
        self._copy_result(result)

    def _copy_result(self, result: SearchResult):
        full_path = config.data_dir / result.path
        if full_path.exists():
            prompt = PromptFile(full_path)
            content = prompt.read_content()
            if clipboard_service.copy_text(content):
                state_service.add_recent_file(result.path)
                usage_service.record_copy(result.path)
                notification_service.success(self, Messages.COPIED)
                if config.copy_auto_hide:
                    QTimer.singleShot(config.copy_hide_delay_ms, self.hide)

    def _copy_result_without_hide(self, result: SearchResult):
        full_path = config.data_dir / result.path
        if full_path.exists():
            prompt = PromptFile(full_path)
            content = prompt.read_content()
            if clipboard_service.copy_text(content):
                state_service.add_recent_file(result.path)
                usage_service.record_copy(result.path)
                notification_service.success(self, "已复制（窗口保持）")

    def _on_escape(self):
        if self.search_input.text():
            self.search_input.clear()
        else:
            self.hide()

    def eventFilter(self, obj, event):
        if obj == self.search_input and event.type() == event.Type.KeyPress:
            if self.search_result_panel.isVisible() and self.search_result_panel.result_list.count() > 0:
                if event.key() == Qt.Key_Down:
                    self.search_result_panel.select_next()
                    return True
                if event.key() == Qt.Key_Up:
                    self.search_result_panel.select_previous()
                    return True
                if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                    result = self.search_result_panel.current_result()
                    if result:
                        if event.modifiers() & Qt.ShiftModifier:
                            self._copy_result_without_hide(result)
                        else:
                            self._copy_result(result)
                    return True
            if event.key() == Qt.Key_Escape and config.esc_hide_enabled:
                if self.search_input.text():
                    self.search_input.clear()
                else:
                    self.hide()
                return True
            if event.key() == Qt.Key_O and event.modifiers() == Qt.ControlModifier:
                result = self.search_result_panel.current_result()
                path = result.path if result else ""
                self.open_main_requested.emit(path)
                self.hide()
                return True
        return super().eventFilter(obj, event)
