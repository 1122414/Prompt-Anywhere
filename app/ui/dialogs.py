from PySide6.QtWidgets import (
    QCheckBox,
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
    QSlider,
    QSpinBox,
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

    def _on_accept(self):
        from app.services.state_service import state_service
        state_service.set_preference("max_recent_files", self.max_recent_spin.value())
        state_service.set_preference("search_selected_bg_color", self.bg_color_input.text())
        state_service.set_preference("copy_auto_hide", self.copy_auto_hide_cb.isChecked())
        state_service.set_preference("copy_hide_delay_ms", self.copy_hide_delay_spin.value())
        state_service.set_preference("esc_hide_enabled", self.esc_hide_cb.isChecked())
        self.accept()

    def _on_reset(self):
        from app.services.state_service import state_service
        state_service.reset_all_preferences()
        self.max_recent_spin.setValue(10)
        self.bg_color_input.setText("#e3f2fd")
        self.copy_auto_hide_cb.setChecked(True)
        self.copy_hide_delay_spin.setValue(200)
        self.esc_hide_cb.setChecked(True)


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
