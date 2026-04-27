from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
)

from app.config import config
from app.constants import AppConstants, Messages
from app.services.file_service import file_service


class CategoryDialog(QDialog):
    def __init__(self, parent=None, category_name: str = ""):
        super().__init__(parent)
        self.setWindowTitle("新建分类" if not category_name else "重命名分类")
        self.setMinimumWidth(300)
        self._old_name = category_name
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.name_input = QLineEdit(self._old_name)
        self.name_input.setPlaceholderText("输入分类名称")
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
            QMessageBox.warning(self, "错误", "分类名称不能为空")
            return
        if name == "全部":
            QMessageBox.warning(self, "错误", "分类名称不能为"全部"")
            return
        if "/" in name or "\\" in name:
            QMessageBox.warning(self, "错误", "分类名称不能包含 / 或 \\")
            return
        if name != self._old_name and name in file_service.get_categories():
            QMessageBox.warning(self, "错误", f'分类"{name}"已存在')
            return
        self.accept()

    def get_name(self) -> str:
        return self.name_input.text().strip()


class PromptDialog(QDialog):
    def __init__(self, parent=None, categories: list = None, default_category: str = ""):
        super().__init__(parent)
        self.setWindowTitle("新建提示词")
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)
        self._setup_ui(categories or [], default_category)

    def _setup_ui(self, categories: list, default_category: str):
        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("输入提示词名称")
        form.addRow("名称:", self.name_input)

        self.category_combo = QComboBox()
        self.category_combo.addItems(categories)
        if default_category and default_category in categories:
            self.category_combo.setCurrentText(default_category)
        form.addRow("分类:", self.category_combo)

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

    def get_category(self) -> str:
        return self.category_combo.currentText()

    def get_extension(self) -> str:
        return ".md" if self.md_radio.isChecked() else ".txt"

    def get_content(self) -> str:
        return self.content_input.toPlainText()
