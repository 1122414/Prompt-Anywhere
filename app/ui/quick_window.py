from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QApplication,
    QLineEdit,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

from app.config import config
from app.constants import Messages
from app.services.clipboard_service import clipboard_service
from app.services.file_service import PromptFile
from app.services.search_service import SearchResult, search_service
from app.services.state_service import state_service
from app.services.usage_service import usage_service
from app.ui.search_result_panel import SearchResultPanel


class QuickWindow(QMainWindow):
    open_main_requested = Signal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{config.app_name} - 快速模式")
        self.setMinimumSize(500, 400)
        self.resize(600, 450)

        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._do_search)
        self._search_worker = None
        self._last_search_keyword = ""

        self._setup_ui()
        self._setup_hotkey()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(Messages.SEARCH_PLACEHOLDER)
        self.search_input.textChanged.connect(self._on_search)
        self.search_input.installEventFilter(self)
        layout.addWidget(self.search_input)

        self.search_result_panel = SearchResultPanel()
        self.search_result_panel.result_selected.connect(self._on_result_selected)
        self.search_result_panel.result_copy_requested.connect(self._on_result_copy)
        self.search_result_panel.escape_pressed.connect(self._on_escape)
        layout.addWidget(self.search_result_panel)

    def _setup_hotkey(self):
        pass

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

    def _on_search(self, text: str):
        self._last_search_keyword = text.strip()
        self._search_timer.stop()
        if not self._last_search_keyword:
            self.search_result_panel.clear_results()
            return
        self._search_timer.start(config.search_debounce_ms)

    def _do_search(self):
        keyword = self._last_search_keyword
        if not keyword:
            self.search_result_panel.clear_results()
            return
        search_id, worker = search_service.search_async(keyword, config.search_case_insensitive)
        worker.setParent(None)
        worker.results_ready.connect(self._on_search_results_ready)
        worker.finished.connect(worker.deleteLater)
        worker.start()
        self._search_worker = worker

    def _on_search_results_ready(self, search_id: int, results: list[SearchResult]):
        if search_id != search_service.get_current_search_id():
            return
        if not self._last_search_keyword:
            self.search_result_panel.clear_results()
            return
        self.search_result_panel.set_results(results, self._last_search_keyword)
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
                if config.copy_auto_hide:
                    QTimer.singleShot(config.copy_hide_delay_ms, self.hide)

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
