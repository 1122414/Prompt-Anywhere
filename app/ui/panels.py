from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from app.config import config
from app.constants import AppConstants, Messages
from app.services.clipboard_service import clipboard_service
from app.services.file_service import PromptFile, file_service
from app.utils.markdown_utils import renderer
from app.utils.syntax_highlighter import MarkdownHighlighter


class CategoryPanel(QWidget):
    category_selected = Signal(str)
    new_category_requested = Signal()
    rename_category_requested = Signal(str)
    delete_category_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        header = QHBoxLayout()
        header_label = QLabel("分类")
        header_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header.addWidget(header_label)
        header.addStretch()

        self.new_btn = QPushButton("+")
        self.new_btn.setFixedSize(28, 28)
        self.new_btn.setToolTip("新建分类")
        self.new_btn.clicked.connect(self.new_category_requested.emit)
        header.addWidget(self.new_btn)
        layout.addLayout(header)

        self.list_widget = QListWidget()
        self.list_widget.setFrameShape(QListWidget.NoFrame)
        self.list_widget.currentTextChanged.connect(self._on_selection_changed)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.list_widget)

    def _on_selection_changed(self, text):
        if text:
            self.category_selected.emit(text)

    def _show_context_menu(self, position):
        item = self.list_widget.itemAt(position)
        if not item or item.text() == "全部":
            return

        menu = QMenu(self)
        rename_action = menu.addAction("重命名")
        delete_action = menu.addAction("删除")

        action = menu.exec(self.list_widget.mapToGlobal(position))
        if action == rename_action:
            self.rename_category_requested.emit(item.text())
        elif action == delete_action:
            self.delete_category_requested.emit(item.text())

    def load_categories(self):
        self.list_widget.clear()
        all_item = QListWidgetItem("全部")
        all_item.setData(Qt.UserRole, "all")
        self.list_widget.addItem(all_item)

        categories = file_service.get_categories()
        for cat in categories:
            item = QListWidgetItem(cat)
            item.setData(Qt.UserRole, "category")
            self.list_widget.addItem(item)

        self.list_widget.setCurrentRow(0)

    def get_current_category(self) -> str:
        item = self.list_widget.currentItem()
        return item.text() if item else "全部"

    def select_category(self, category: str):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.text() == category:
                self.list_widget.setCurrentItem(item)
                break


class PromptListPanel(QWidget):
    prompt_selected = Signal(object)
    new_prompt_requested = Signal()
    rename_prompt_requested = Signal(object)
    delete_prompt_requested = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._current_prompts = []

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        header = QHBoxLayout()
        header_label = QLabel("提示词")
        header_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header.addWidget(header_label)
        header.addStretch()

        self.new_btn = QPushButton("+")
        self.new_btn.setFixedSize(28, 28)
        self.new_btn.setToolTip("新建提示词")
        self.new_btn.clicked.connect(self.new_prompt_requested.emit)
        header.addWidget(self.new_btn)
        layout.addLayout(header)

        self.list_widget = QListWidget()
        self.list_widget.setFrameShape(QListWidget.NoFrame)
        self.list_widget.currentItemChanged.connect(self._on_item_changed)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.list_widget)

        self.empty_label = QLabel(Messages.EMPTY_STATE_PROMPTS)
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet("color: #888; padding: 20px;")
        self.empty_label.hide()
        layout.addWidget(self.empty_label)

    def _on_item_changed(self, current, previous):
        if current:
            data = current.data(Qt.UserRole)
            if isinstance(data, PromptFile):
                self.prompt_selected.emit(data)

    def _show_context_menu(self, position):
        item = self.list_widget.itemAt(position)
        if not item:
            return

        prompt = item.data(Qt.UserRole)
        if not isinstance(prompt, PromptFile):
            return

        menu = QMenu(self)
        rename_action = menu.addAction("重命名")
        delete_action = menu.addAction("删除")

        action = menu.exec(self.list_widget.mapToGlobal(position))
        if action == rename_action:
            self.rename_prompt_requested.emit(prompt)
        elif action == delete_action:
            self.delete_prompt_requested.emit(prompt)

    def load_prompts(self, prompts: list):
        self._current_prompts = prompts
        self.list_widget.clear()

        if not prompts:
            self.empty_label.show()
            self.list_widget.hide()
        else:
            self.empty_label.hide()
            self.list_widget.show()
            for prompt in prompts:
                item = QListWidgetItem(f"{prompt.name}{prompt.extension}")
                item.setData(Qt.UserRole, prompt)
                self.list_widget.addItem(item)

    def get_current_prompt(self) -> PromptFile:
        item = self.list_widget.currentItem()
        if item:
            return item.data(Qt.UserRole)
        return None

    def select_prompt(self, prompt: PromptFile):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            data = item.data(Qt.UserRole)
            if isinstance(data, PromptFile) and data.path == prompt.path:
                self.list_widget.setCurrentItem(item)
                break


class EditorPanel(QWidget):
    content_changed = Signal()
    save_requested = Signal()
    copy_requested = Signal()
    export_requested = Signal()
    delete_requested = Signal()
    mode_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_prompt = None
        self._is_modified = False
        self._current_mode = config.default_mode
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        toolbar = QHBoxLayout()

        self.mode_edit_btn = QPushButton("编辑模式")
        self.mode_edit_btn.setCheckable(True)
        self.mode_edit_btn.clicked.connect(lambda: self.set_mode(AppConstants.MODE_EDIT))
        toolbar.addWidget(self.mode_edit_btn)

        self.mode_preview_btn = QPushButton("渲染模式")
        self.mode_preview_btn.setCheckable(True)
        self.mode_preview_btn.clicked.connect(lambda: self.set_mode(AppConstants.MODE_PREVIEW))
        toolbar.addWidget(self.mode_preview_btn)

        toolbar.addStretch()

        self.copy_btn = QPushButton("复制")
        self.copy_btn.clicked.connect(self.copy_requested.emit)
        toolbar.addWidget(self.copy_btn)

        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self.save_requested.emit)
        toolbar.addWidget(self.save_btn)

        self.export_btn = QPushButton("导出")
        self.export_btn.clicked.connect(self.export_requested.emit)
        toolbar.addWidget(self.export_btn)

        self.delete_btn = QPushButton("删除")
        self.delete_btn.clicked.connect(self.delete_requested.emit)
        toolbar.addWidget(self.delete_btn)

        layout.addLayout(toolbar)

        self.editor = QPlainTextEdit()
        self.editor.textChanged.connect(self._on_text_changed)
        self.highlighter = MarkdownHighlighter(self.editor.document())
        layout.addWidget(self.editor)

        self.preview = QTextBrowser()
        self.preview.setOpenExternalLinks(True)
        layout.addWidget(self.preview)

        self.empty_label = QLabel("选择一个提示词以查看内容")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet("color: #888; padding: 40px;")
        layout.addWidget(self.empty_label)

        self._update_visibility()

    def _on_text_changed(self):
        if self._current_prompt:
            self._is_modified = True
            self._update_title()
            self.content_changed.emit()

    def _update_title(self):
        if self._current_prompt:
            marker = " *" if self._is_modified else ""
            self.window().setWindowTitle(f"{self._current_prompt.name}{marker} - {AppConstants.APP_NAME}")

    def _is_txt_file(self) -> bool:
        return self._current_prompt is not None and self._current_prompt.extension == ".txt"

    def _update_visibility(self):
        has_prompt = self._current_prompt is not None
        is_txt = self._is_txt_file()

        self.editor.setVisible(has_prompt and (self._current_mode == AppConstants.MODE_EDIT or is_txt))
        self.preview.setVisible(has_prompt and self._current_mode == AppConstants.MODE_PREVIEW and not is_txt)
        self.empty_label.setVisible(not has_prompt)

        self.mode_edit_btn.setChecked(self._current_mode == AppConstants.MODE_EDIT)
        self.mode_preview_btn.setChecked(self._current_mode == AppConstants.MODE_PREVIEW)
        self.mode_preview_btn.setVisible(has_prompt and not is_txt)

        self.copy_btn.setEnabled(has_prompt)
        self.save_btn.setEnabled(has_prompt and self._is_modified)
        self.export_btn.setEnabled(has_prompt)
        self.delete_btn.setEnabled(has_prompt)

    def set_mode(self, mode: str):
        if mode not in (AppConstants.MODE_EDIT, AppConstants.MODE_PREVIEW):
            return
        self._current_mode = mode
        if mode == AppConstants.MODE_PREVIEW and self._current_prompt:
            text = self.editor.toPlainText()
            html = renderer.render(text)
            self.preview.setHtml(html)
        self._update_visibility()
        self.mode_changed.emit(mode)

    def load_prompt(self, prompt: PromptFile):
        if self._is_modified:
            return False

        self._current_prompt = prompt
        self._is_modified = False

        if prompt:
            content = prompt.read_content()
            self.editor.setPlainText(content)
            if prompt.extension == ".txt":
                self._current_mode = AppConstants.MODE_EDIT
            self.set_mode(self._current_mode)
        else:
            self.editor.clear()
            self.preview.clear()

        self._update_visibility()
        self._update_title()
        return True

    def get_content(self) -> str:
        return self.editor.toPlainText()

    def is_modified(self) -> bool:
        return self._is_modified

    def mark_saved(self):
        self._is_modified = False
        self._update_title()
        self._update_visibility()

    def get_current_prompt(self) -> PromptFile:
        return self._current_prompt

    def check_unsaved(self) -> str:
        if self._is_modified:
            reply = QMessageBox.question(
                self,
                "未保存的更改",
                Messages.UNSAVED_CHANGES,
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save,
            )
            if reply == QMessageBox.Save:
                return AppConstants.SAVE
            elif reply == QMessageBox.Discard:
                return AppConstants.DISCARD
            else:
                return AppConstants.CANCEL
        return AppConstants.SAVE
