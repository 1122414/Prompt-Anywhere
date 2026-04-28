import re

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent, QFont
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from app.config import config
from app.services.file_service import PromptFile
from app.services.search_service import SearchResult


class SearchResultPanel(QWidget):
    result_selected = Signal(SearchResult)
    result_copy_requested = Signal(SearchResult)
    escape_pressed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._results: list[SearchResult] = []
        self._keyword = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.splitter = QSplitter(Qt.Horizontal)

        self.result_list = QListWidget()
        self.result_list.setSpacing(1)
        self.result_list.setStyleSheet("""
            QListWidget {
                border: none;
                background: #fafafa;
            }
            QListWidget::item {
                border-bottom: 1px solid #eee;
                padding: 6px 8px;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
            }
            QListWidget::item:hover {
                background-color: #f0f0f0;
            }
        """)
        self.result_list.currentItemChanged.connect(self._on_selection_changed)
        self.splitter.addWidget(self.result_list)

        self.preview = QTextBrowser()
        self.preview.setOpenExternalLinks(False)
        self.preview.setStyleSheet("border: none; padding: 12px; font-size: 13px;")
        self.splitter.addWidget(self.preview)

        self.splitter.setSizes([300, 500])
        layout.addWidget(self.splitter)

    def set_results(self, results: list[SearchResult], keyword: str):
        self._results = results
        self._keyword = keyword
        self.result_list.clear()
        for result in results:
            item = QListWidgetItem()
            item.setText(result.filename)
            item.setToolTip(f"{result.category or '根目录'} / {result.filename}")
            item.setData(Qt.UserRole, result)
            self.result_list.addItem(item)
        if self.result_list.count() > 0:
            self.result_list.setCurrentRow(0)

    def clear_results(self):
        self._results = []
        self._keyword = ""
        self.result_list.clear()
        self.preview.clear()

    def current_result(self) -> SearchResult | None:
        current = self.result_list.currentRow()
        if 0 <= current < len(self._results):
            return self._results[current]
        if self._results:
            return self._results[0]
        return None

    def select_first(self):
        if self.result_list.count() > 0:
            self.result_list.setCurrentRow(0)

    def select_next(self):
        current = self.result_list.currentRow()
        if current < self.result_list.count() - 1:
            self.result_list.setCurrentRow(current + 1)

    def select_previous(self):
        current = self.result_list.currentRow()
        if current > 0:
            self.result_list.setCurrentRow(current - 1)

    def _on_selection_changed(self, current, previous):
        if current is None:
            return
        row = self.result_list.row(current)
        if 0 <= row < len(self._results):
            result = self._results[row]
            self._show_preview(result)

    def _show_preview(self, result: SearchResult):
        full_path = config.data_dir / result.path
        if not full_path.exists():
            self.preview.setPlainText("(文件不存在)")
            return
        try:
            content = full_path.read_text(encoding=config.file_encoding)
        except Exception:
            self.preview.setPlainText("(无法读取文件)")
            return
        self.preview.setPlainText(content)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if event.modifiers() == Qt.ControlModifier:
                result = self.current_result()
                if result:
                    self.result_copy_requested.emit(result)
            else:
                result = self.current_result()
                if result:
                    self.result_selected.emit(result)
        elif event.key() == Qt.Key_Escape:
            self.escape_pressed.emit()
        elif event.key() == Qt.Key_Down:
            self.select_next()
            event.accept()
        elif event.key() == Qt.Key_Up:
            self.select_previous()
            event.accept()
        else:
            super().keyPressEvent(event)
