from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.config import config
from app.services.ai_template_service import TemplateVariable, ai_template_service


class AITemplateDialog(QDialog):
    template_applied = Signal(str, list)

    def __init__(self, content: str, parent=None):
        super().__init__(parent)
        self._original_content = content
        self._variables: list[TemplateVariable] = []
        self._templated_content = content
        self.setWindowTitle("AI 模板助手")
        self.setMinimumSize(800, 600)
        self._setup_ui()
        self._detect_variables()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # 原始内容
        layout.addWidget(QLabel("原始提示词:"))
        self.original_edit = QPlainTextEdit()
        self.original_edit.setPlainText(self._original_content)
        self.original_edit.setReadOnly(True)
        self.original_edit.setMaximumHeight(150)
        layout.addWidget(self.original_edit)

        # 按钮行
        btn_layout = QHBoxLayout()
        self.rule_btn = QPushButton("仅规则识别")
        self.rule_btn.clicked.connect(self._detect_rule_only)
        btn_layout.addWidget(self.rule_btn)

        self.ai_btn = QPushButton("AI 识别")
        self.ai_btn.clicked.connect(self._detect_ai_only)
        btn_layout.addWidget(self.ai_btn)

        self.hybrid_btn = QPushButton("混合识别")
        self.hybrid_btn.clicked.connect(self._detect_hybrid)
        btn_layout.addWidget(self.hybrid_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # 变量列表
        layout.addWidget(QLabel("识别到的变量:"))
        self.var_table = QTableWidget()
        self.var_table.setColumnCount(3)
        self.var_table.setHorizontalHeaderLabels(["变量名", "类型", "默认值"])
        self.var_table.setColumnWidth(0, 200)
        self.var_table.setColumnWidth(1, 100)
        self.var_table.setColumnWidth(2, 300)
        layout.addWidget(self.var_table)

        # 模板化结果
        layout.addWidget(QLabel("模板化结果:"))
        self.result_edit = QPlainTextEdit()
        self.result_edit.setReadOnly(True)
        layout.addWidget(self.result_edit)

        # 底部按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.Apply | QDialogButtonBox.Cancel
        )
        buttons.button(QDialogButtonBox.Apply).setText("应用模板")
        buttons.button(QDialogButtonBox.Apply).clicked.connect(self._on_apply)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _detect_variables(self):
        if not config.ai_template_enabled:
            self._variables = ai_template_service.detect_variables_rule(self._original_content)
        else:
            self._variables = ai_template_service.detect_variables(self._original_content)
        self._update_ui()

    def _detect_rule_only(self):
        self._variables = ai_template_service.detect_variables_rule(self._original_content)
        self._update_ui()

    def _detect_ai_only(self):
        if not config.ai_template_enabled:
            QMessageBox.information(self, "提示", "AI 模板助手未启用或未配置")
            return
        self._variables = ai_template_service.detect_variables_ai(self._original_content)
        if not self._variables:
            QMessageBox.information(self, "提示", "AI 未能识别到变量，已回退到规则识别")
            self._variables = ai_template_service.detect_variables_rule(self._original_content)
        self._update_ui()

    def _detect_hybrid(self):
        self._detect_variables()

    def _update_ui(self):
        self.var_table.setRowCount(len(self._variables))
        for i, var in enumerate(self._variables):
            self.var_table.setItem(i, 0, QTableWidgetItem(var.name))
            self.var_table.setItem(i, 1, QTableWidgetItem(var.var_type))
            self.var_table.setItem(i, 2, QTableWidgetItem(var.default))

        self._templated_content = ai_template_service.apply_variables(
            self._original_content, self._variables
        )
        self.result_edit.setPlainText(self._templated_content)

    def _on_apply(self):
        self.template_applied.emit(self._templated_content, self._variables)
        self.accept()
