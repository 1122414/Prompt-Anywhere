import logging
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from app.config import config
from app.services.clipboard_service import clipboard_service
from app.services.composer_service import composer_service
from app.services.file_service import file_service

logger = logging.getLogger(__name__)


class ComposerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Composer 组合器")
        self.setMinimumSize(config.composer_window_width, config.composer_window_height)
        self._setup_ui()
        self._load_available_files()
        self._update_preview()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        splitter = QSplitter(Qt.Horizontal)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.addWidget(QLabel("可选提示词"))

        self._available_list = QListWidget()
        self._available_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self._available_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self._available_list.customContextMenuRequested.connect(self._show_available_context_menu)
        left_layout.addWidget(self._available_list)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("搜索提示词...")
        self._search_input.textChanged.connect(self._filter_available)
        left_layout.addWidget(self._search_input)

        splitter.addWidget(left_panel)

        middle_panel = QWidget()
        middle_layout = QVBoxLayout(middle_panel)
        middle_layout.addWidget(QLabel("已选择片段"))

        self._selected_list = QListWidget()
        self._selected_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self._selected_list.customContextMenuRequested.connect(self._show_selected_context_menu)
        middle_layout.addWidget(self._selected_list)

        control_layout = QHBoxLayout()
        self._add_btn = QPushButton("加入 →")
        self._add_btn.clicked.connect(self._on_add)
        control_layout.addWidget(self._add_btn)

        self._remove_btn = QPushButton("← 移除")
        self._remove_btn.clicked.connect(self._on_remove)
        control_layout.addWidget(self._remove_btn)

        self._up_btn = QPushButton("↑ 上移")
        self._up_btn.clicked.connect(self._on_move_up)
        control_layout.addWidget(self._up_btn)

        self._down_btn = QPushButton("↓ 下移")
        self._down_btn.clicked.connect(self._on_move_down)
        control_layout.addWidget(self._down_btn)

        self._clear_btn = QPushButton("清空")
        self._clear_btn.clicked.connect(self._on_clear)
        control_layout.addWidget(self._clear_btn)

        middle_layout.addLayout(control_layout)

        splitter.addWidget(middle_panel)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.addWidget(QLabel("组合预览（可编辑）"))

        self._preview = QPlainTextEdit()
        self._preview.setReadOnly(False)
        self._preview.textChanged.connect(self._on_preview_changed)
        right_layout.addWidget(self._preview)

        splitter.addWidget(right_panel)

        splitter.setSizes([200, 200, 400])
        layout.addWidget(splitter)

        button_layout = QHBoxLayout()

        self._copy_btn = QPushButton("复制组合结果")
        self._copy_btn.clicked.connect(self._on_copy)
        button_layout.addWidget(self._copy_btn)

        self._use_template_btn = QPushButton("使用模板变量")
        self._use_template_btn.clicked.connect(self._on_use_template)
        self._use_template_btn.setEnabled(False)
        button_layout.addWidget(self._use_template_btn)

        self._export_btn = QPushButton("导出md")
        self._export_btn.clicked.connect(self._on_export)
        button_layout.addWidget(self._export_btn)

        self._save_btn = QPushButton("保存组合")
        self._save_btn.clicked.connect(self._on_save)
        button_layout.addWidget(self._save_btn)

        self._close_btn = QPushButton("关闭")
        self._close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self._close_btn)

        layout.addLayout(button_layout)

    def _load_available_files(self):
        self._available_list.clear()
        for prompt in file_service.iter_all_prompts():
            item = QListWidgetItem()
            rel_path = prompt.path.relative_to(config.data_dir).as_posix()
            item.setText(f"{prompt.name} ({prompt.extension})")
            item.setData(Qt.UserRole, rel_path)
            item.setToolTip(rel_path)
            self._available_list.addItem(item)

    def _filter_available(self, text):
        for i in range(self._available_list.count()):
            item = self._available_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    def _on_add(self):
        for item in self._available_list.selectedItems():
            rel_path = item.data(Qt.UserRole)
            if composer_service.add_file(rel_path):
                self._selected_list.addItem(item.clone())
        self._update_preview()

    def _on_remove(self):
        for item in self._selected_list.selectedItems():
            rel_path = item.data(Qt.UserRole)
            composer_service.remove_file(rel_path)
            self._selected_list.takeItem(self._selected_list.row(item))
        self._update_preview()

    def _on_move_up(self):
        current = self._selected_list.currentRow()
        if composer_service.move_up(current):
            item = self._selected_list.takeItem(current)
            self._selected_list.insertItem(current - 1, item)
            self._selected_list.setCurrentRow(current - 1)
            self._update_preview()

    def _on_move_down(self):
        current = self._selected_list.currentRow()
        if composer_service.move_down(current):
            item = self._selected_list.takeItem(current)
            self._selected_list.insertItem(current + 1, item)
            self._selected_list.setCurrentRow(current + 1)
            self._update_preview()

    def _on_clear(self):
        composer_service.clear()
        self._selected_list.clear()
        self._update_preview()

    def _update_preview(self):
        content = composer_service.build()
        self._preview.blockSignals(True)
        self._preview.setPlainText(content)
        self._preview.blockSignals(False)

        from app.services.template_service import template_service
        variables = template_service.extract_variables(content)
        self._use_template_btn.setEnabled(len(variables) > 0)

    def _on_preview_changed(self):
        from app.services.template_service import template_service
        content = self._preview.toPlainText()
        variables = template_service.extract_variables(content)
        self._use_template_btn.setEnabled(len(variables) > 0)

    def _get_content(self):
        return self._preview.toPlainText()

    def _on_copy(self):
        content = self._get_content()
        if content:
            clipboard_service.copy_text(content)
            QMessageBox.information(self, "复制成功", "已复制组合结果到剪贴板")

    def _on_use_template(self):
        content = self._get_content()
        if not content:
            return

        from app.services.template_service import template_service
        variables = template_service.extract_variables(content)

        if not variables:
            QMessageBox.information(self, "提示", "组合结果中没有模板变量")
            return

        from app.ui.dialogs import TemplateDialog
        dialog = TemplateDialog(self, filename="组合结果", variables=variables, content=content)
        dialog.exec()

    def _on_export(self):
        content = self._get_content()
        if not content:
            QMessageBox.warning(self, "提示", "没有内容可导出")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出组合结果", "组合结果.md", "Markdown Files (*.md);;Text Files (*.txt)"
        )
        if file_path:
            Path(file_path).write_text(content, encoding=config.file_encoding)
            QMessageBox.information(self, "导出成功", f"已导出到：{file_path}")

    def _on_save(self):
        name, ok = QInputDialog.getText(self, "保存组合", "组合名称：")
        if ok and name:
            content = self._get_content()
            if not content:
                QMessageBox.warning(self, "提示", "没有内容可保存")
                return
            try:
                save_dir = config.composer_save_dir
                save_dir.mkdir(parents=True, exist_ok=True)
                file_path = save_dir / f"{name}.md"
                file_path.write_text(content, encoding=config.file_encoding)
                QMessageBox.information(self, "保存成功", f"已保存到：{file_path}")
                self.accept()
            except Exception as e:
                QMessageBox.warning(self, "保存失败", str(e))

    def _show_available_context_menu(self, position):
        menu = QMenu(self)
        menu.addAction("加入组合器", self._on_add)
        menu.exec(self._available_list.mapToGlobal(position))

    def _show_selected_context_menu(self, position):
        menu = QMenu(self)
        menu.addAction("移除", self._on_remove)
        menu.addAction("上移", self._on_move_up)
        menu.addAction("下移", self._on_move_down)
        menu.exec(self._selected_list.mapToGlobal(position))
