import re

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.ui.theme import THEME_COLOR_KEYS, THEME_COLOR_LABELS


class ThemeEditorDialog(QDialog):
    def __init__(self, name: str, palette: dict, theme_id: str = "", parent=None):
        super().__init__(parent)
        self._palette = dict(palette)
        self._existing_id = theme_id
        self._color_buttons = {}
        self.setWindowTitle("编辑自定义主题" if theme_id else "创建自定义主题")
        self.setMinimumSize(680, 620)
        self._setup_ui(name)
        self._update_preview()

    def _setup_ui(self, name: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(14)

        title = QLabel("主题工作台")
        title.setObjectName("dialogTitle")
        subtitle = QLabel("选择核心界面颜色。所有修改都会在下方实时预览。")
        subtitle.setObjectName("mutedText")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        identity = QFormLayout()
        self.name_input = QLineEdit(name)
        self.id_input = QLineEdit(self._existing_id or self._slugify(name) or "my-theme")
        self.id_input.setPlaceholderText("例如 ocean-blue")
        self.id_input.setEnabled(not bool(self._existing_id))
        identity.addRow("主题名称", self.name_input)
        identity.addRow("主题标识", self.id_input)
        layout.addLayout(identity)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        color_host = QWidget()
        color_host.setObjectName("themeColorGrid")
        grid = QGridLayout(color_host)
        grid.setContentsMargins(4, 4, 4, 4)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        for index, key in enumerate(THEME_COLOR_KEYS):
            row = index // 2
            column = (index % 2) * 2
            label = QLabel(THEME_COLOR_LABELS[key])
            button = QPushButton(self._palette[key].upper())
            button.setMinimumWidth(130)
            button.clicked.connect(lambda checked=False, color_key=key: self._pick_color(color_key))
            self._color_buttons[key] = button
            grid.addWidget(label, row, column)
            grid.addWidget(button, row, column + 1)
        scroll.setWidget(color_host)
        layout.addWidget(scroll, 1)

        self.preview = QWidget()
        self.preview.setObjectName("themePreview")
        preview_layout = QVBoxLayout(self.preview)
        preview_layout.setContentsMargins(18, 16, 18, 16)
        preview_header = QHBoxLayout()
        self.preview_title = QLabel("Prompt Anywhere")
        self.preview_title.setObjectName("previewTitle")
        self.preview_chip = QLabel("主题预览")
        self.preview_chip.setObjectName("previewChip")
        preview_header.addWidget(self.preview_title)
        preview_header.addStretch()
        preview_header.addWidget(self.preview_chip)
        preview_layout.addLayout(preview_header)
        self.preview_input = QLineEdit("搜索 Prompt、标签或内容…")
        self.preview_input.setReadOnly(True)
        preview_layout.addWidget(self.preview_input)
        preview_actions = QHBoxLayout()
        self.preview_secondary = QPushButton("次要操作")
        self.preview_primary = QPushButton("主操作")
        preview_actions.addStretch()
        preview_actions.addWidget(self.preview_secondary)
        preview_actions.addWidget(self.preview_primary)
        preview_layout.addLayout(preview_actions)
        layout.addWidget(self.preview)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("保存主题")
        buttons.button(QDialogButtonBox.Cancel).setText("取消")
        buttons.accepted.connect(self._accept_if_valid)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _slugify(self, value: str) -> str:
        return re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip()).strip("-").lower()

    def _pick_color(self, key: str):
        initial = QColor(self._palette[key])
        color = QColorDialog.getColor(initial, self, THEME_COLOR_LABELS[key])
        if color.isValid():
            self._palette[key] = color.name().upper()
            self._color_buttons[key].setText(self._palette[key])
            self._update_preview()

    def _update_preview(self):
        p = self._palette
        for key, button in self._color_buttons.items():
            color = p[key]
            text = "#FFFFFF" if QColor(color).lightness() < 128 else "#15181C"
            button.setStyleSheet(
                f"QPushButton {{ background: {color}; color: {text}; border: 1px solid {p['hairline_strong']}; }}"
            )
        self.preview.setStyleSheet(
            f"""
            QWidget#themePreview {{
                background: {p["surface"]};
                border: 1px solid {p["hairline"]};
                border-radius: 12px;
            }}
            QLabel#previewTitle {{
                color: {p["ink"]};
                font-size: 16px;
                font-weight: 700;
            }}
            QLabel#previewChip {{
                color: {p["accent_hover"]};
                background: {p["surface_active"]};
                border: 1px solid {p["hairline"]};
                border-radius: 9px;
                padding: 3px 8px;
            }}
            QLineEdit {{
                background: {p["surface_elevated"]};
                color: {p["body"]};
                border: 1px solid {p["hairline"]};
                border-radius: 8px;
                padding: 8px 10px;
            }}
            QPushButton {{
                background: {p["surface_panel"]};
                color: {p["body"]};
                border: 1px solid {p["hairline"]};
                border-radius: 8px;
                padding: 7px 12px;
            }}
            """
        )
        self.preview_primary.setStyleSheet(
            f"background: {p['primary']}; color: {p['on_primary']}; border-color: {p['primary']};"
        )

    def _accept_if_valid(self):
        if not self.name_input.text().strip():
            self.name_input.setFocus()
            return
        if not self.id_input.text().strip():
            self.id_input.setFocus()
            return
        self.accept()

    def theme_data(self) -> tuple[str, str, dict]:
        return self.id_input.text().strip(), self.name_input.text().strip(), dict(self._palette)
