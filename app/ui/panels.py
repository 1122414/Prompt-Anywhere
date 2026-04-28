from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from app.config import config
from app.constants import AppConstants, Messages
from app.services.file_service import PromptFile
from app.utils.image_utils import save_pasted_image
from app.utils.markdown_utils import renderer
from app.utils.syntax_highlighter import MarkdownHighlighter


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
        self._current_mode = config.default_view_mode
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
        self.editor.installEventFilter(self)
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
            self.window().setWindowTitle(f"{self._current_prompt.name}{marker} - {config.app_name}")

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
            self.preview.setSearchPaths([str(self._current_prompt.path.parent)])
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
            self.editor.blockSignals(True)
            self.editor.setPlainText(content)
            self.editor.blockSignals(False)
            self._is_modified = False
            if prompt.extension == ".txt":
                self._current_mode = AppConstants.MODE_EDIT
            self.set_mode(self._current_mode)
        else:
            self.editor.blockSignals(True)
            self.editor.clear()
            self.editor.blockSignals(False)
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

    def update_prompt_path(self, prompt: PromptFile) -> None:
        self._current_prompt = prompt
        self._update_title()

    def eventFilter(self, obj, event):
        if obj == self.editor and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key_V and event.modifiers() == Qt.ControlModifier:
                if self._handle_paste():
                    return True
        return super().eventFilter(obj, event)

    def _handle_paste(self) -> bool:
        if not self._current_prompt:
            return False
        if self._current_prompt.extension != ".md":
            QMessageBox.information(
                self,
                "无法插入图片",
                "当前文件是 txt 格式，无法插入图片。请转换或新建 md 文件。",
            )
            return False

        from PySide6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        mime = clipboard.mimeData()

        if mime.hasText() and not mime.hasImage() and not mime.urls():
            return False

        image_path = save_pasted_image(mime, self._current_prompt.path)
        if image_path:
            cursor = self.editor.textCursor()
            markdown_link = f"![pasted image]({image_path})"
            cursor.insertText(markdown_link)
            self._on_text_changed()
            return True

        return False

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
