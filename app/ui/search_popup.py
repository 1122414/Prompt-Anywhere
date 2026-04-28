from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

from app.config import config
from app.services.search_service import SearchResult
from app.ui.search_result_panel import SearchResultPanel


class SearchPopupWindow(QMainWindow):
    result_selected = Signal(SearchResult)
    result_copy_requested = Signal(SearchResult)
    escape_pressed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("搜索结果")
        self.setMinimumSize(700, 450)
        self.resize(800, 500)
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self._setup_ui()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        self.panel = SearchResultPanel()
        self.panel.result_selected.connect(self.result_selected)
        self.panel.result_copy_requested.connect(self.result_copy_requested)
        self.panel.escape_pressed.connect(self.escape_pressed)
        layout.addWidget(self.panel)

    def show_results(self, results: list[SearchResult], keyword: str):
        self.panel.set_results(results, keyword)
        self.show()
        self.raise_()
        self.activateWindow()
        if self.panel.result_list.count() > 0:
            self.panel.select_first()

    def clear(self):
        self.panel.clear_results()
        self.hide()

    def closeEvent(self, event):
        self.hide()
        event.ignore()
