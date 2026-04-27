from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QRadioButton,
    QVBoxLayout,
)


class FolderDialog(QDialog):
    def __init__(self, parent=None, folder_path: str = "", folder_name: str = ""):
        super().__init__(parent)
        self._folder_path = folder_path
        self._old_name = folder_name
        self.setWindowTitle("重命名文件夹" if folder_name else "新建文件夹")
        self.setMinimumWidth(300)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        if self._folder_path:
            path_label = QLabel(f"父目录: {self._folder_path or '根目录'}")
            path_label.setStyleSheet("color: #888;")
            layout.addWidget(path_label)

        form = QFormLayout()
        self.name_input = QLineEdit(self._old_name)
        self.name_input.setPlaceholderText("输入文件夹名称")
        form.addRow("名称:", self.name_input)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "错误", "文件夹名称不能为空")
            return
        if "/" in name or "\\" in name:
            QMessageBox.warning(self, "错误", "名称不能包含 / 或 \\")
            return
        self.accept()

    def get_name(self) -> str:
        return self.name_input.text().strip()


class PromptDialog(QDialog):
    def __init__(self, parent=None, parent_path: str = ""):
        super().__init__(parent)
        self._parent_path = parent_path
        self.setWindowTitle("新建提示词")
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        path_label = QLabel(f"保存位置: {self._parent_path or '根目录'}")
        path_label.setStyleSheet("color: #888;")
        layout.addWidget(path_label)

        form = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("输入提示词名称")
        form.addRow("名称:", self.name_input)

        type_layout = QHBoxLayout()
        self.md_radio = QRadioButton(".md (Markdown)")
        self.md_radio.setChecked(True)
        self.txt_radio = QRadioButton(".txt (纯文本)")
        type_layout.addWidget(self.md_radio)
        type_layout.addWidget(self.txt_radio)
        type_layout.addStretch()
        form.addRow("格式:", type_layout)

        layout.addLayout(form)

        self.content_input = QPlainTextEdit()
        self.content_input.setPlaceholderText("输入提示词内容...")
        layout.addWidget(QLabel("内容:"))
        layout.addWidget(self.content_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "错误", "提示词名称不能为空")
            return
        if "/" in name or "\\" in name:
            QMessageBox.warning(self, "错误", "名称不能包含 / 或 \\")
            return
        self.accept()

    def get_name(self) -> str:
        return self.name_input.text().strip()

    def get_extension(self) -> str:
        return ".md" if self.md_radio.isChecked() else ".txt"

    def get_content(self) -> str:
        return self.content_input.toPlainText()
