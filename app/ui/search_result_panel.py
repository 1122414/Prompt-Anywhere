import re

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.config import config
from app.services.search_service import SearchResult


class SearchResultWidget(QWidget):
    def __init__(self, result: SearchResult, keyword: str, parent=None):
        super().__init__(parent)
        self.result = result
        self.keyword = keyword
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        self.name_label = QLabel(self._highlight(self.result.filename, self.keyword))
        self.name_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(self.name_label)

        category_text = self.result.category if self.result.category else "根目录"
        path_text = f"{category_text} / {self.result.filename}"
        self.path_label = QLabel(path_text)
        self.path_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self.path_label)

        if self.result.snippets:
            snippet_text = self._highlight(self.result.snippets[0], self.keyword)
            self.snippet_label = QLabel(snippet_text)
            self.snippet_label.setStyleSheet("color: #666; font-size: 12px; padding-top: 2px;")
            self.snippet_label.setWordWrap(True)
            layout.addWidget(self.snippet_label)

    def _highlight(self, text: str, keyword: str) -> str:
        import html
        text = html.escape(text)
        if not keyword or not config.search_highlight_enabled:
            return text
        pattern = re.escape(keyword)
        flags = re.IGNORECASE if config.search_case_insensitive else 0
        return re.sub(
            f"({pattern})",
            r'<span style="background-color: #ffeb3b; color: #000;">\1</span>',
            text,
            flags=flags,
        )


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

        self.list_widget = QListWidget()
        self.list_widget.setSpacing(2)
        self.list_widget.setStyleSheet("""
            QListWidget {
                border: none;
                background: transparent;
            }
            QListWidget::item {
                border-bottom: 1px solid #e0e0e0;
                padding: 0px;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
        """)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.list_widget)

    def set_results(self, results: list[SearchResult], keyword: str):
        self._results = results
        self._keyword = keyword
        self.list_widget.clear()
        for result in results:
            item = QListWidgetItem(self.list_widget)
            widget = SearchResultWidget(result, keyword)
            item.setSizeHint(widget.sizeHint())
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, widget)

    def clear_results(self):
        self._results = []
        self._keyword = ""
        self.list_widget.clear()

    def current_result(self) -> SearchResult | None:
        current = self.list_widget.currentRow()
        if 0 <= current < len(self._results):
            return self._results[current]
        if self._results:
            return self._results[0]
        return None

    def select_first(self):
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def select_next(self):
        current = self.list_widget.currentRow()
        if current < self.list_widget.count() - 1:
            self.list_widget.setCurrentRow(current + 1)
        elif self.list_widget.count() > 0 and current < 0:
            self.list_widget.setCurrentRow(0)

    def select_previous(self):
        current = self.list_widget.currentRow()
        if current > 0:
            self.list_widget.setCurrentRow(current - 1)

    def _on_item_clicked(self, item: QListWidgetItem):
        index = self.list_widget.row(item)
        if 0 <= index < len(self._results):
            self.result_selected.emit(self._results[index])

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
        elif event.key() == Qt.Key_Up:
            self.select_previous()
        else:
            super().keyPressEvent(event)
