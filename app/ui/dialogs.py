from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.config import config


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


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumWidth(400)
        self._setup_ui()
        self._load_preferences()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.max_recent_spin = QSpinBox()
        self.max_recent_spin.setMinimum(1)
        self.max_recent_spin.setMaximum(20)
        self.max_recent_spin.setValue(10)
        form.addRow("最近使用最多保留条数:", self.max_recent_spin)

        self.bg_color_input = QLineEdit()
        self.bg_color_input.setPlaceholderText("#e3f2fd")
        form.addRow("搜索选中背景颜色:", self.bg_color_input)

        self.copy_auto_hide_cb = QCheckBox("复制后自动隐藏窗口")
        self.copy_auto_hide_cb.setChecked(True)
        form.addRow(self.copy_auto_hide_cb)

        self.copy_hide_delay_spin = QSpinBox()
        self.copy_hide_delay_spin.setMinimum(0)
        self.copy_hide_delay_spin.setMaximum(5000)
        self.copy_hide_delay_spin.setSingleStep(50)
        self.copy_hide_delay_spin.setSuffix(" ms")
        form.addRow("复制后隐藏延迟:", self.copy_hide_delay_spin)

        self.esc_hide_cb = QCheckBox("Esc 隐藏窗口")
        self.esc_hide_cb.setChecked(True)
        form.addRow(self.esc_hide_cb)

        self.show_template_btn_cb = QCheckBox("显示使用模板按钮")
        self.show_template_btn_cb.setChecked(True)
        form.addRow(self.show_template_btn_cb)

        self.show_composer_btn_cb = QCheckBox("显示组合器按钮")
        self.show_composer_btn_cb.setChecked(True)
        form.addRow(self.show_composer_btn_cb)

        self.enable_builtin_cb = QCheckBox("启用内置模板")
        self.enable_builtin_cb.setChecked(True)
        form.addRow(self.enable_builtin_cb)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)

        reset_btn = QPushButton("重置所有设置")
        reset_btn.clicked.connect(self._on_reset)
        buttons.addButton(reset_btn, QDialogButtonBox.ResetRole)

        layout.addWidget(buttons)

    def _load_preferences(self):
        from app.services.state_service import state_service
        self.max_recent_spin.setValue(int(state_service.get_preference("max_recent_files", 10)))
        self.bg_color_input.setText(state_service.get_preference("search_selected_bg_color", "#e3f2fd"))
        self.copy_auto_hide_cb.setChecked(state_service.get_preference("copy_auto_hide", True))
        self.copy_hide_delay_spin.setValue(int(state_service.get_preference("copy_hide_delay_ms", 200)))
        self.esc_hide_cb.setChecked(state_service.get_preference("esc_hide_enabled", True))
        self.show_template_btn_cb.setChecked(state_service.get_preference("show_template_button", True))
        self.show_composer_btn_cb.setChecked(state_service.get_preference("show_composer_button", True))
        self.enable_builtin_cb.setChecked(state_service.get_preference("enable_builtin_templates", True))

    def _on_accept(self):
        from app.services.state_service import state_service
        state_service.set_preference("max_recent_files", self.max_recent_spin.value())
        state_service.set_preference("search_selected_bg_color", self.bg_color_input.text())
        state_service.set_preference("copy_auto_hide", self.copy_auto_hide_cb.isChecked())
        state_service.set_preference("copy_hide_delay_ms", self.copy_hide_delay_spin.value())
        state_service.set_preference("esc_hide_enabled", self.esc_hide_cb.isChecked())
        state_service.set_preference("show_template_button", self.show_template_btn_cb.isChecked())
        state_service.set_preference("show_composer_button", self.show_composer_btn_cb.isChecked())
        state_service.set_preference("enable_builtin_templates", self.enable_builtin_cb.isChecked())
        self.accept()

    def _on_reset(self):
        from app.services.state_service import state_service
        state_service.reset_all_preferences()
        self.max_recent_spin.setValue(10)
        self.bg_color_input.setText("#e3f2fd")
        self.copy_auto_hide_cb.setChecked(True)
        self.copy_hide_delay_spin.setValue(200)
        self.esc_hide_cb.setChecked(True)
        self.show_template_btn_cb.setChecked(True)
        self.show_composer_btn_cb.setChecked(True)
        self.enable_builtin_cb.setChecked(True)


class VariableNameDialog(QDialog):
    def __init__(self, parent=None, selected_text: str = ""):
        super().__init__(parent)
        self._selected_text = selected_text
        self.setWindowTitle("输入变量名")
        self.setMinimumWidth(400)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        if self._selected_text:
            text_label = QLabel(f"选中的文本：{self._selected_text}")
            text_label.setStyleSheet("color: #666; padding: 4px;")
            layout.addWidget(text_label)

        form = QFormLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("输入变量名（仅限字母、数字、下划线）")
        form.addRow("变量名:", self.name_input)
        layout.addLayout(form)

        quick_label = QLabel("常用变量名：")
        layout.addWidget(quick_label)

        quick_layout = QHBoxLayout()
        quick_layout.setSpacing(4)

        common_names = [
            "project_name", "company", "target_role", "task",
            "requirements", "constraints", "output_format"
        ]

        for name in common_names:
            btn = QPushButton(name)
            btn.setStyleSheet("padding: 2px 6px; font-size: 11px;")
            btn.clicked.connect(lambda checked, n=name: self.name_input.setText(n))
            quick_layout.addWidget(btn)

        quick_layout.addStretch()
        layout.addLayout(quick_layout)

        quick_layout2 = QHBoxLayout()
        quick_layout2.setSpacing(4)

        common_names2 = [
            "tone", "length", "code", "text",
            "background", "acceptance_criteria", "forbidden"
        ]

        for name in common_names2:
            btn = QPushButton(name)
            btn.setStyleSheet("padding: 2px 6px; font-size: 11px;")
            btn.clicked.connect(lambda checked, n=name: self.name_input.setText(n))
            quick_layout2.addWidget(btn)

        quick_layout2.addStretch()
        layout.addLayout(quick_layout2)

        self.validation_label = QLabel("")
        self.validation_label.setStyleSheet("color: red;")
        layout.addWidget(self.validation_label)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.name_input.textChanged.connect(self._validate_input)

    def _validate_input(self, text):
        from app.services.template_service import template_service
        is_valid, error_msg = template_service.validate_variable_name(text)
        if text and not is_valid:
            self.validation_label.setText(error_msg)
        else:
            self.validation_label.setText("")

    def _on_accept(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "错误", "变量名不能为空")
            return

        from app.services.template_service import template_service
        is_valid, error_msg = template_service.validate_variable_name(name)
        if not is_valid:
            QMessageBox.warning(self, "错误", error_msg)
            return

        self.accept()

    def get_variable_name(self) -> str:
        return self.name_input.text().strip()


class TemplateDialog(QDialog):
    def __init__(self, parent=None, filename: str = "", variables: list[str] = None, content: str = ""):
        super().__init__(parent)
        self._filename = filename
        self._variables = variables or []
        self._content = content
        self._result = ""
        self.setWindowTitle("使用模板")
        self.setMinimumSize(config.template_dialog_width, config.template_dialog_height)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        if self._filename:
            name_label = QLabel(f"文件：{self._filename}")
            name_label.setStyleSheet("color: #666; padding: 4px;")
            layout.addWidget(name_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        self._form_layout = QFormLayout(scroll_widget)

        self._inputs: dict[str, QWidget] = {}
        for var_name in self._variables:
            if self._is_multiline_variable(var_name):
                input_widget = QPlainTextEdit()
                input_widget.setMaximumHeight(100)
                input_widget.setPlaceholderText(f"输入 {var_name}")
            else:
                input_widget = QLineEdit()
                input_widget.setPlaceholderText(f"输入 {var_name}")
            self._inputs[var_name] = input_widget
            self._form_layout.addRow(f"{var_name}:", input_widget)

        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        preview_label = QLabel("预览：")
        layout.addWidget(preview_label)
        self._preview = QPlainTextEdit()
        self._preview.setReadOnly(True)
        self._preview.setMaximumHeight(150)
        layout.addWidget(self._preview)

        button_layout = QHBoxLayout()
        self._generate_btn = QPushButton("生成预览")
        self._generate_btn.clicked.connect(self._on_generate)
        button_layout.addWidget(self._generate_btn)

        self._copy_btn = QPushButton("复制结果")
        self._copy_btn.clicked.connect(self._on_copy)
        self._copy_btn.setEnabled(False)
        button_layout.addWidget(self._copy_btn)

        self._export_btn = QPushButton("导出结果")
        self._export_btn.clicked.connect(self._on_export)
        self._export_btn.setEnabled(False)
        button_layout.addWidget(self._export_btn)

        self._cancel_btn = QPushButton("取消")
        self._cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self._cancel_btn)

        layout.addLayout(button_layout)

    def _is_multiline_variable(self, var_name: str) -> bool:
        multiline_keywords = [
            "requirements", "description", "content", "text", "code",
            "background", "constraints", "forbidden", "acceptance_criteria",
        ]
        return any(kw in var_name.lower() for kw in multiline_keywords)

    def _get_values(self) -> dict[str, str]:
        values: dict[str, str] = {}
        for var_name, input_widget in self._inputs.items():
            if isinstance(input_widget, QPlainTextEdit):
                values[var_name] = input_widget.toPlainText()
            elif isinstance(input_widget, QLineEdit):
                values[var_name] = input_widget.text()
        return values

    def _on_generate(self):
        values = self._get_values()
        empty_vars = [k for k, v in values.items() if not v.strip()]
        if empty_vars:
            QMessageBox.warning(self, "提示", f"请填写以下变量：{', '.join(empty_vars)}")
            return
        from app.services.template_service import template_service
        self._result = template_service.render(self._content, values)
        self._preview.setPlainText(self._result)
        self._copy_btn.setEnabled(True)
        self._export_btn.setEnabled(True)

    def _on_copy(self):
        if self._result:
            from app.services.clipboard_service import clipboard_service
            clipboard_service.copy_text(self._result)
            QMessageBox.information(self, "复制成功", "已复制到剪贴板")

    def _on_export(self):
        if not self._result:
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出结果", f"{self._filename}_filled.md",
            "Markdown Files (*.md);;Text Files (*.txt)",
        )
        if file_path:
            from pathlib import Path
            Path(file_path).write_text(self._result, encoding=config.file_encoding)
            QMessageBox.information(self, "导出成功", f"已导出到：{file_path}")

    def get_result(self) -> str:
        return self._result


class BuiltinTemplateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("导入内置模板")
        self.setMinimumSize(500, 400)
        self._setup_ui()
        self._load_templates()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        list_label = QLabel("选择要导入的模板：")
        layout.addWidget(list_label)

        self._template_list = QListWidget()
        self._template_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        layout.addWidget(self._template_list)

        category_layout = QHBoxLayout()
        category_layout.addWidget(QLabel("导入到分类："))

        self._category_combo = QComboBox()
        self._load_categories()
        category_layout.addWidget(self._category_combo)

        self._new_category_btn = QPushButton("新建分类")
        self._new_category_btn.clicked.connect(self._on_new_category)
        category_layout.addWidget(self._new_category_btn)

        layout.addLayout(category_layout)

        button_layout = QHBoxLayout()
        self._import_btn = QPushButton("导入选中")
        self._import_btn.clicked.connect(self._on_import)
        button_layout.addWidget(self._import_btn)

        self._cancel_btn = QPushButton("取消")
        self._cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self._cancel_btn)

        layout.addLayout(button_layout)

    def _load_categories(self):
        from app.services.file_service import file_service
        categories = file_service.get_categories()
        self._category_combo.clear()
        self._category_combo.addItems(categories)

    def _load_templates(self):
        from app.services.builtin_template_service import builtin_template_service
        templates = builtin_template_service.list_templates()

        self._template_list.clear()
        for template in templates:
            item = QListWidgetItem()
            item.setText(f"{template['category']}/{template['name']}" if template["category"] else template["name"])
            item.setData(Qt.ItemDataRole.UserRole, template["path"])
            self._template_list.addItem(item)

    def _on_new_category(self):
        name, ok = QInputDialog.getText(self, "新建分类", "分类名称：")
        if ok and name:
            from app.services.file_service import file_service
            if file_service.create_category(name):
                self._load_categories()
                self._category_combo.setCurrentText(name)
            else:
                QMessageBox.warning(self, "错误", f"创建分类失败：{name}")

    def _on_import(self):
        selected_items = self._template_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "提示", "请先选择要导入的模板")
            return

        category = self._category_combo.currentText()
        if not category:
            QMessageBox.warning(self, "提示", "请选择目标分类")
            return

        template_paths = [item.data(Qt.ItemDataRole.UserRole) for item in selected_items]

        from app.services.builtin_template_service import builtin_template_service
        success_count, errors = builtin_template_service.import_templates(template_paths, category)

        if success_count > 0:
            QMessageBox.information(self, "导入成功", f"成功导入 {success_count} 个模板到 {category}")
            self.accept()
        else:
            QMessageBox.warning(self, "导入失败", "\n".join(errors) if errors else "导入失败")
