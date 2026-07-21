import json
import logging

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSlider,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt

from app.config import config
from app.ui.theme import (
    BUILTIN_PALETTES,
    custom_themes,
    default_theme_variant,
    delete_custom_theme,
    muted_label_stylesheet,
    palette_for_theme,
    save_custom_theme,
    theme_display_label,
    theme_options,
    theme_variant_options,
    theme_variant_preference_key,
    validate_custom_theme,
)
from app.ui.theme_widgets import ThemeVariantPreview

logger = logging.getLogger(__name__)


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumSize(860, 640)
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 14)
        layout.setSpacing(14)

        heading = QLabel("偏好设置")
        heading.setObjectName("dialogTitle")
        caption = QLabel("调整外观、快捷键、数据安全与智能功能。设置会保存在本机。")
        caption.setObjectName("mutedText")
        layout.addWidget(heading)
        layout.addWidget(caption)

        content = QHBoxLayout()
        content.setSpacing(14)
        self.settings_nav = QListWidget()
        self.settings_nav.setObjectName("settingsNav")
        self.settings_nav.setFixedWidth(154)
        self.settings_stack = QStackedWidget()
        pages = [
            ("常规", self._create_general_tab()),
            ("路径", self._create_paths_tab()),
            ("快捷键", self._create_hotkeys_tab()),
            ("窗口", self._create_window_tab()),
            ("数据安全", self._create_data_safety_tab()),
            ("功能开关", self._create_features_tab()),
            ("搜索设置", self._create_search_tab()),
            ("语义搜索", self._create_semantic_search_tab()),
            ("AI 模板助手", self._create_ai_template_tab()),
            ("模型设置", self._create_model_tab()),
            ("关于", self._create_about_tab()),
        ]
        for label, page in pages:
            self.settings_nav.addItem(label)
            self.settings_stack.addWidget(page)
        self.settings_nav.currentRowChanged.connect(self.settings_stack.setCurrentIndex)
        self.settings_nav.setCurrentRow(0)
        content.addWidget(self.settings_nav)
        content.addWidget(self.settings_stack, 1)
        layout.addLayout(content, 1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.button(QDialogButtonBox.Ok).setText("保存")
        buttons.button(QDialogButtonBox.Cancel).setText("取消")
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _create_general_tab(self):
        tab = QWidget()
        layout = QFormLayout(tab)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setHorizontalSpacing(18)
        layout.setVerticalSpacing(12)

        self.theme_combo = QComboBox()
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        theme_row = QHBoxLayout()
        theme_row.setSpacing(8)
        theme_row.addWidget(self.theme_combo, 1)
        self.theme_edit_btn = QPushButton("自定义")
        self.theme_edit_btn.clicked.connect(self._edit_theme)
        theme_row.addWidget(self.theme_edit_btn)
        self.theme_more_btn = QPushButton("导入")
        self.theme_more_btn.clicked.connect(self._import_theme)
        theme_row.addWidget(self.theme_more_btn)
        layout.addRow("界面主题:", theme_row)

        self.theme_variant_combo = QComboBox()
        self.theme_variant_combo.currentIndexChanged.connect(self._update_theme_preview)
        self.theme_variant_host = QWidget()
        variant_layout = QHBoxLayout(self.theme_variant_host)
        variant_layout.setContentsMargins(0, 0, 0, 0)
        variant_layout.addWidget(self.theme_variant_combo)
        layout.addRow("主题背景:", self.theme_variant_host)
        self.theme_variant_label = layout.labelForField(self.theme_variant_host)

        self.theme_preview = ThemeVariantPreview()
        layout.addRow("", self.theme_preview)

        theme_hint = QLabel("三形态主题会同时切换背景与强调色；保存后主窗口和快速窗口立即更新。")
        theme_hint.setObjectName("mutedText")
        theme_hint.setWordWrap(True)
        layout.addRow("", theme_hint)

        theme_actions = QHBoxLayout()
        export_btn = QPushButton("导出当前主题")
        export_btn.clicked.connect(self._export_theme)
        delete_btn = QPushButton("删除自定义主题")
        delete_btn.clicked.connect(self._delete_theme)
        theme_actions.addWidget(export_btn)
        theme_actions.addWidget(delete_btn)
        theme_actions.addStretch()
        layout.addRow("", theme_actions)

        self.start_minimized_cb = QCheckBox("启动后最小化到托盘")
        layout.addRow(self.start_minimized_cb)

        self.close_to_tray_cb = QCheckBox("关闭窗口时最小化到托盘")
        layout.addRow(self.close_to_tray_cb)

        self.copy_auto_hide_cb = QCheckBox("复制后自动隐藏窗口")
        layout.addRow(self.copy_auto_hide_cb)

        self.copy_hide_delay_spin = QSpinBox()
        self.copy_hide_delay_spin.setMinimum(0)
        self.copy_hide_delay_spin.setMaximum(5000)
        self.copy_hide_delay_spin.setSingleStep(50)
        self.copy_hide_delay_spin.setSuffix(" ms")
        layout.addRow("复制后隐藏延迟:", self.copy_hide_delay_spin)

        self.esc_hide_cb = QCheckBox("Esc 隐藏窗口")
        layout.addRow(self.esc_hide_cb)

        self.start_with_windows_cb = QCheckBox("开机自动启动")
        layout.addRow(self.start_with_windows_cb)

        return tab

    def _reload_theme_options(self, selected: str = ""):
        if not selected:
            selected = self.theme_combo.currentData() if self.theme_combo.count() else "light"
        self.theme_combo.blockSignals(True)
        self.theme_combo.clear()
        for key, label in theme_options().items():
            self.theme_combo.addItem(label, key)
        index = self.theme_combo.findData(selected)
        self.theme_combo.setCurrentIndex(index if index >= 0 else 0)
        self.theme_combo.blockSignals(False)
        self._on_theme_changed()

    def _on_theme_changed(self):
        from app.services.state_service import state_service

        theme_id = self.theme_combo.currentData() or "light"
        preferred = state_service.get_preference(
            theme_variant_preference_key(theme_id),
            default_theme_variant(theme_id),
        )
        self._reload_theme_variants(preferred)
        self._update_theme_preview()

    def _reload_theme_variants(self, selected: str = ""):
        theme_id = self.theme_combo.currentData() or "light"
        options = theme_variant_options(theme_id)
        self.theme_variant_combo.blockSignals(True)
        self.theme_variant_combo.clear()
        for key, label in options.items():
            self.theme_variant_combo.addItem(label, key)
        index = self.theme_variant_combo.findData(selected)
        self.theme_variant_combo.setCurrentIndex(index if index >= 0 else 0)
        self.theme_variant_combo.blockSignals(False)
        visible = bool(options)
        self.theme_variant_host.setVisible(visible)
        if self.theme_variant_label:
            self.theme_variant_label.setVisible(visible)

    def _update_theme_preview(self):
        theme_id = self.theme_combo.currentData() or "light"
        variant_id = self.theme_variant_combo.currentData() or ""
        self.theme_preview.set_theme(theme_id, variant_id)

    def _edit_theme(self):
        from app.ui.theme_editor_dialog import ThemeEditorDialog
        theme_id = self.theme_combo.currentData() or "light"
        variant_id = self.theme_variant_combo.currentData() or ""
        custom = custom_themes()
        existing = custom.get(theme_id)
        name = existing.get("name", "") if existing else theme_options().get(theme_id, "自定义主题")
        name = name.replace(" · 自定义", "")
        dialog = ThemeEditorDialog(
            name=f"{name} 副本" if not existing else name,
            palette=palette_for_theme(theme_id, variant_id),
            theme_id=theme_id if existing else "",
            parent=self,
        )
        if dialog.exec() != QDialog.Accepted:
            return
        new_id, new_name, palette = dialog.theme_data()
        success, result = save_custom_theme(new_id, new_name, palette)
        if not success:
            QMessageBox.warning(self, "主题保存失败", result)
            return
        self._reload_theme_options(result)

    def _delete_theme(self):
        theme_id = self.theme_combo.currentData()
        if theme_id in BUILTIN_PALETTES:
            QMessageBox.information(self, "内置主题", "内置主题不能删除，可以点击“自定义”创建副本。")
            return
        if not theme_id or not delete_custom_theme(theme_id):
            return
        self._reload_theme_options("light")

    def _export_theme(self):
        theme_id = self.theme_combo.currentData() or "light"
        variant_id = self.theme_variant_combo.currentData() or ""
        value = custom_themes().get(theme_id, {})
        payload = {
            "id": theme_id if theme_id not in BUILTIN_PALETTES else f"{theme_id}-custom",
            "name": value.get(
                "name",
                theme_display_label(theme_id, variant_id).replace(" · 自定义", ""),
            ),
            "palette": palette_for_theme(theme_id, variant_id),
        }
        path, _ = QFileDialog.getSaveFileName(
            self, "导出主题", f"{payload['id']}.json", "Prompt Anywhere 主题 (*.json)"
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
        except OSError as e:
            QMessageBox.warning(self, "导出失败", str(e))

    def _import_theme(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "导入主题", "", "Prompt Anywhere 主题 (*.json)"
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            QMessageBox.warning(self, "导入失败", f"无法读取主题文件：{e}")
            return
        valid, error = validate_custom_theme(payload)
        if not valid:
            QMessageBox.warning(self, "导入失败", error)
            return
        success, result = save_custom_theme(
            str(payload.get("id", "")), str(payload.get("name", "")), payload.get("palette", {})
        )
        if not success:
            QMessageBox.warning(self, "导入失败", result)
            return
        self._reload_theme_options(result)

    def _create_paths_tab(self):
        tab = QWidget()
        layout = QFormLayout(tab)
        layout.addRow("数据目录:", self._create_path_row("data_dir", "./data"))
        layout.addRow("导出目录:", self._create_path_row("export_dir", "./exports"))
        layout.addRow("备份目录:", self._create_path_row("backup_dir", "./backups"))
        layout.addRow("日志目录:", self._create_path_row("log_dir", "./logs"))
        return tab

    def _create_path_row(self, attr_name: str, placeholder: str):
        row_layout = QHBoxLayout()
        input_widget = QLineEdit()
        input_widget.setPlaceholderText(placeholder)
        setattr(self, f"{attr_name}_input", input_widget)
        row_layout.addWidget(input_widget)
        browse_btn = QPushButton("浏览")
        browse_btn.clicked.connect(lambda checked=None, w=input_widget: self._browse_dir(w))
        row_layout.addWidget(browse_btn)
        return row_layout

    def _create_hotkeys_tab(self):
        tab = QWidget()
        layout = QFormLayout(tab)

        self.hotkey_input = QLineEdit()
        self.hotkey_input.setPlaceholderText("ctrl+alt+p")
        layout.addRow("快速模式快捷键:", self.hotkey_input)

        self.main_hotkey_input = QLineEdit()
        self.main_hotkey_input.setPlaceholderText("ctrl+alt+m")
        layout.addRow("主窗口快捷键:", self.main_hotkey_input)

        hint_label = QLabel("提示: 快捷键格式为 modifier+key，例如 ctrl+alt+p")
        self.zoom_in_shortcut_input = QLineEdit()
        self.zoom_in_shortcut_input.setPlaceholderText("Ctrl+=")
        layout.addRow("放大快捷键:", self.zoom_in_shortcut_input)

        self.zoom_out_shortcut_input = QLineEdit()
        self.zoom_out_shortcut_input.setPlaceholderText("Ctrl+-")
        layout.addRow("缩小快捷键:", self.zoom_out_shortcut_input)

        self.zoom_reset_shortcut_input = QLineEdit()
        self.zoom_reset_shortcut_input.setPlaceholderText("Ctrl+0")
        layout.addRow("重置缩放快捷键:", self.zoom_reset_shortcut_input)

        hint_label.setStyleSheet(muted_label_stylesheet())
        layout.addRow(hint_label)

        return tab

    def _create_window_tab(self):
        tab = QWidget()
        layout = QFormLayout(tab)

        self.always_on_top_cb = QCheckBox("窗口置顶")
        layout.addRow(self.always_on_top_cb)

        opacity_layout = QHBoxLayout()
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setMinimum(60)
        self.opacity_slider.setMaximum(100)
        opacity_layout.addWidget(self.opacity_slider)
        self.opacity_label = QLabel("100%")
        self.opacity_slider.valueChanged.connect(
            lambda v: self.opacity_label.setText(f"{v}%")
        )
        opacity_layout.addWidget(self.opacity_label)
        layout.addRow("透明度:", opacity_layout)

        self.remember_position_cb = QCheckBox("记住窗口位置")
        layout.addRow(self.remember_position_cb)

        self.remember_size_cb = QCheckBox("记住窗口大小")
        layout.addRow(self.remember_size_cb)

        return tab

    def _create_data_safety_tab(self):
        tab = QWidget()
        layout = QFormLayout(tab)

        self.auto_backup_cb = QCheckBox("启用自动备份")
        layout.addRow(self.auto_backup_cb)

        self.backup_interval_spin = QSpinBox()
        self.backup_interval_spin.setMinimum(1)
        self.backup_interval_spin.setMaximum(168)
        self.backup_interval_spin.setSuffix(" 小时")
        layout.addRow("自动备份间隔:", self.backup_interval_spin)

        self.max_backup_spin = QSpinBox()
        self.max_backup_spin.setMinimum(1)
        self.max_backup_spin.setMaximum(100)
        layout.addRow("最大备份数量:", self.max_backup_spin)

        self.history_enabled_cb = QCheckBox("保存前创建历史版本")
        layout.addRow(self.history_enabled_cb)

        self.max_versions_spin = QSpinBox()
        self.max_versions_spin.setMinimum(1)
        self.max_versions_spin.setMaximum(100)
        layout.addRow("最大历史版本数:", self.max_versions_spin)

        manage_btn = QPushButton("管理备份")
        manage_btn.clicked.connect(self._manage_backups)
        layout.addRow(manage_btn)

        return tab

    def _manage_backups(self):
        from app.services.backup_service import backup_service
        from pathlib import Path
        try:
            backup_service.initialize(Path("backups"))
            backups = backup_service.list_backups()
            if not backups:
                QMessageBox.information(self, "备份管理", "暂无备份文件")
                return
            backup_list = "\n".join([f"{i+1}. {b.name}" for i, b in enumerate(backups)])
            reply = QMessageBox.question(
                self, "备份管理",
                f"共 {len(backups)} 个备份:\n\n{backup_list}\n\n是否清理旧备份（保留最新备份）？",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            if reply == QMessageBox.Yes:
                backup_service.cleanup_old_backups()
                QMessageBox.information(self, "备份管理", "旧备份已清理")
        except Exception as e:
            QMessageBox.warning(self, "备份管理", f"操作失败: {e}")

    def _create_features_tab(self):
        tab = QWidget()
        layout = QFormLayout(tab)

        self.template_enabled_cb = QCheckBox("启用模板变量")
        layout.addRow(self.template_enabled_cb)

        self.composer_enabled_cb = QCheckBox("启用 Composer")
        layout.addRow(self.composer_enabled_cb)

        self.builtin_templates_cb = QCheckBox("启用内置模板")
        layout.addRow(self.builtin_templates_cb)

        return tab

    def _create_search_tab(self):
        tab = QWidget()
        layout = QFormLayout(tab)

        self.search_enable_pinyin_cb = QCheckBox("启用拼音搜索")
        layout.addRow(self.search_enable_pinyin_cb)

        self.search_enable_initials_cb = QCheckBox("启用首字母搜索")
        layout.addRow(self.search_enable_initials_cb)

        self.search_enable_fuzzy_cb = QCheckBox("启用模糊搜索")
        layout.addRow(self.search_enable_fuzzy_cb)

        self.search_debounce_spin = QSpinBox()
        self.search_debounce_spin.setMinimum(50)
        self.search_debounce_spin.setMaximum(500)
        self.search_debounce_spin.setSingleStep(10)
        self.search_debounce_spin.setSuffix(" ms")
        layout.addRow("搜索防抖时间:", self.search_debounce_spin)

        self.search_max_results_spin = QSpinBox()
        self.search_max_results_spin.setMinimum(10)
        self.search_max_results_spin.setMaximum(500)
        layout.addRow("最大搜索结果数:", self.search_max_results_spin)

        self.search_fuzzy_mode_combo = QLineEdit()
        self.search_fuzzy_mode_combo.setPlaceholderText("balanced")
        layout.addRow("模糊搜索模式 (strict/balanced/loose):", self.search_fuzzy_mode_combo)

        return tab

    def _create_semantic_search_tab(self):
        tab = QWidget()
        layout = QFormLayout(tab)

        self.semantic_search_enabled_cb = QCheckBox("启用语义搜索（实验性功能）")
        layout.addRow(self.semantic_search_enabled_cb)

        self.semantic_search_provider_input = QLineEdit()
        self.semantic_search_provider_input.setPlaceholderText("api 或 local")
        layout.addRow("Embedding 提供者:", self.semantic_search_provider_input)

        self.semantic_search_api_url_input = QLineEdit()
        self.semantic_search_api_url_input.setPlaceholderText("https://api.openai.com/v1")
        layout.addRow("API Base URL:", self.semantic_search_api_url_input)

        self.semantic_search_api_key_input = QLineEdit()
        self.semantic_search_api_key_input.setEchoMode(QLineEdit.Password)
        layout.addRow("API Key:", self.semantic_search_api_key_input)

        self.semantic_search_api_model_input = QLineEdit()
        self.semantic_search_api_model_input.setPlaceholderText("text-embedding-3-small")
        layout.addRow("API 模型:", self.semantic_search_api_model_input)

        self.semantic_search_local_model_input = QLineEdit()
        self.semantic_search_local_model_input.setPlaceholderText("BAAI/bge-small-zh-v1.5")
        layout.addRow("本地模型:", self.semantic_search_local_model_input)

        self.semantic_search_top_k_spin = QSpinBox()
        self.semantic_search_top_k_spin.setMinimum(5)
        self.semantic_search_top_k_spin.setMaximum(100)
        layout.addRow("Top-K:", self.semantic_search_top_k_spin)

        return tab

    def _create_ai_template_tab(self):
        tab = QWidget()
        layout = QFormLayout(tab)

        self.ai_template_enabled_cb = QCheckBox("启用 AI 模板助手")
        layout.addRow(self.ai_template_enabled_cb)

        self.ai_template_provider_input = QLineEdit()
        self.ai_template_provider_input.setPlaceholderText("openai_compatible 或 ollama")
        layout.addRow("AI 提供者:", self.ai_template_provider_input)

        self.ai_template_base_url_input = QLineEdit()
        layout.addRow("Base URL:", self.ai_template_base_url_input)

        self.ai_template_api_key_input = QLineEdit()
        self.ai_template_api_key_input.setEchoMode(QLineEdit.Password)
        layout.addRow("API Key:", self.ai_template_api_key_input)

        self.ai_template_model_input = QLineEdit()
        layout.addRow("模型:", self.ai_template_model_input)

        self.ai_template_temperature_spin = QSpinBox()
        self.ai_template_temperature_spin.setMinimum(0)
        self.ai_template_temperature_spin.setMaximum(20)
        self.ai_template_temperature_spin.setSuffix(" * 0.1")
        layout.addRow("温度参数:", self.ai_template_temperature_spin)

        self.ai_template_detection_mode_input = QLineEdit()
        self.ai_template_detection_mode_input.setPlaceholderText("rule / ai / hybrid")
        layout.addRow("检测模式:", self.ai_template_detection_mode_input)

        return tab

    def _create_model_tab(self):
        tab = QWidget()
        layout = QFormLayout(tab)
        layout.addRow(QLabel("以下为通用模型配置，修改后需重启应用"))

        self.model_provider_input = QLineEdit()
        self.model_provider_input.setPlaceholderText("如 openai / ollama")
        layout.addRow("模型提供商:", self.model_provider_input)

        self.model_name_input = QLineEdit()
        self.model_name_input.setPlaceholderText("如 gpt-4 / llama3")
        layout.addRow("模型名称:", self.model_name_input)

        self.model_api_key_input = QLineEdit()
        self.model_api_key_input.setEchoMode(QLineEdit.Password)
        self.model_api_key_input.setPlaceholderText("API Key")
        layout.addRow("API Key:", self.model_api_key_input)

        self.model_base_url_input = QLineEdit()
        self.model_base_url_input.setPlaceholderText("如 https://api.openai.com/v1")
        layout.addRow("API 地址:", self.model_base_url_input)

        self.model_temperature_spin = QSpinBox()
        self.model_temperature_spin.setMinimum(0)
        self.model_temperature_spin.setMaximum(20)
        self.model_temperature_spin.setSuffix(" * 0.1")
        layout.addRow("温度参数:", self.model_temperature_spin)

        return tab

    def _create_about_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        layout.addWidget(QLabel(f"应用名称: {config.app_name}"))
        layout.addWidget(QLabel(f"版本: {config.app_version}"))
        layout.addWidget(QLabel(f"数据目录: {config.data_dir}"))
        layout.addWidget(QLabel("配置文件: app_config.json"))
        layout.addWidget(QLabel("日志目录: ./logs"))

        layout.addStretch()

        open_log_btn = QPushButton("打开日志目录")
        open_log_btn.clicked.connect(self._open_log_dir)
        layout.addWidget(open_log_btn)

        export_diag_btn = QPushButton("导出诊断信息")
        export_diag_btn.clicked.connect(self._export_diagnostics)
        layout.addWidget(export_diag_btn)

        return tab

    def _export_diagnostics(self):
        from app.services.diagnostics_service import diagnostics_service
        from pathlib import Path
        try:
            output = diagnostics_service.export_diagnostics(Path("./logs"))
            QMessageBox.information(self, "导出成功", f"诊断信息已导出到:\n{output}")
        except Exception as e:
            QMessageBox.warning(self, "导出失败", str(e))

    def _browse_dir(self, line_edit):
        dir_path = QFileDialog.getExistingDirectory(self, "选择目录")
        if dir_path:
            line_edit.setText(dir_path)

    def _open_log_dir(self):
        import os
        import subprocess
        from pathlib import Path

        log_dir = Path("./logs").resolve()
        log_dir.mkdir(parents=True, exist_ok=True)
        try:
            if os.name == "nt":
                os.startfile(str(log_dir))
            else:
                subprocess.Popen(["xdg-open", str(log_dir)])
        except Exception as e:
            logger.warning(f"Failed to open log directory: {e}")
            QMessageBox.warning(self, "错误", f"无法打开日志目录: {e}")

    def _load_settings(self):
        from app.services.config_service import config_service
        from app.services.state_service import state_service

        self._reload_theme_options()
        theme = state_service.get_preference("ui_theme", "light")
        theme_index = self.theme_combo.findData(theme)
        self.theme_combo.setCurrentIndex(theme_index if theme_index >= 0 else 0)
        self._on_theme_changed()

        self.start_minimized_cb.setChecked(
            config_service.get("behavior.start_minimized", False)
        )
        self.close_to_tray_cb.setChecked(
            config_service.get("behavior.close_to_tray", True)
        )
        self.copy_auto_hide_cb.setChecked(config.copy_auto_hide)
        self.copy_hide_delay_spin.setValue(config.copy_hide_delay_ms)
        self.esc_hide_cb.setChecked(config.esc_hide_enabled)

        self.start_with_windows_cb.setChecked(
            config_service.get("behavior.start_with_windows", False)
        )

        self.data_dir_input.setText(str(config.data_dir))
        self.export_dir_input.setText(str(config.export_dir))
        self.backup_dir_input.setText(
            config_service.get("storage.backup_dir", "./backups")
        )
        self.log_dir_input.setText(
            config_service.get("storage.log_dir", "./logs")
        )

        self.hotkey_input.setText(config_service.get("behavior.hotkey", config.hotkey))
        self.main_hotkey_input.setText(
            config_service.get("behavior.main_hotkey", "ctrl+alt+m")
        )
        self.zoom_in_shortcut_input.setText(state_service.get_preference("zoom_in_shortcut", "Ctrl+="))
        self.zoom_out_shortcut_input.setText(state_service.get_preference("zoom_out_shortcut", "Ctrl+-"))
        self.zoom_reset_shortcut_input.setText(state_service.get_preference("zoom_reset_shortcut", "Ctrl+0"))

        parent = self.parentWidget()
        self.always_on_top_cb.setChecked(
            getattr(parent, "_always_on_top", config.always_on_top)
        )
        self.opacity_slider.setValue(
            int(getattr(parent, "_window_opacity", config.default_window_opacity) * 100)
        )
        self.remember_position_cb.setChecked(
            config_service.get("window.remember_position", True)
        )
        self.remember_size_cb.setChecked(
            config_service.get("window.remember_size", True)
        )

        self.auto_backup_cb.setChecked(
            config_service.get("backup.auto_backup_enabled", True)
        )
        self.backup_interval_spin.setValue(
            config_service.get("backup.auto_backup_interval_hours", 24)
        )
        self.max_backup_spin.setValue(
            config_service.get("backup.max_backup_count", 20)
        )
        self.history_enabled_cb.setChecked(
            config_service.get("history.enabled", True)
        )
        self.max_versions_spin.setValue(
            config_service.get("history.max_versions_per_file", 20)
        )

        self.template_enabled_cb.setChecked(
            config_service.get("features.template_variables", True)
        )
        self.composer_enabled_cb.setChecked(
            config_service.get("features.composer", True)
        )
        self.builtin_templates_cb.setChecked(
            config_service.get("features.builtin_templates", True)
        )

        self.search_enable_pinyin_cb.setChecked(config.search_enable_pinyin)
        self.search_enable_initials_cb.setChecked(config.search_enable_initials)
        self.search_enable_fuzzy_cb.setChecked(config.search_enable_fuzzy)
        self.search_debounce_spin.setValue(config.search_debounce_ms)
        self.search_max_results_spin.setValue(config.search_max_results)
        self.search_fuzzy_mode_combo.setText(config.search_fuzzy_mode)

        self.semantic_search_enabled_cb.setChecked(config.semantic_search_enabled)
        self.semantic_search_provider_input.setText(config.semantic_search_provider)
        self.semantic_search_api_url_input.setText(config.semantic_search_api_base_url)
        self.semantic_search_api_key_input.setText(config.semantic_search_api_key)
        self.semantic_search_api_model_input.setText(config.semantic_search_api_model)
        self.semantic_search_local_model_input.setText(config.semantic_search_local_model)
        self.semantic_search_top_k_spin.setValue(config.semantic_search_top_k)

        self.ai_template_enabled_cb.setChecked(config.ai_template_enabled)
        self.ai_template_provider_input.setText(config.ai_template_provider)
        self.ai_template_base_url_input.setText(config.ai_template_base_url)
        self.ai_template_api_key_input.setText(config.ai_template_api_key)
        self.ai_template_model_input.setText(config.ai_template_model)
        self.ai_template_temperature_spin.setValue(int(config.ai_template_temperature * 10))
        self.ai_template_detection_mode_input.setText(config.ai_template_detection_mode)

        self.model_provider_input.setText(config.model_provider)
        self.model_name_input.setText(config.model_name)
        self.model_api_key_input.setText(config.model_api_key)
        self.model_base_url_input.setText(config.model_base_url)
        self.model_temperature_spin.setValue(int(config.model_temperature * 10))

    def _on_accept(self):
        from app.services.config_service import config_service
        from app.services.state_service import state_service

        theme_id = self.theme_combo.currentData() or "light"
        state_service.set_preference("ui_theme", theme_id)
        variant_id = self.theme_variant_combo.currentData() or ""
        if variant_id in theme_variant_options(theme_id):
            state_service.set_preference(
                theme_variant_preference_key(theme_id),
                variant_id,
            )

        config_service.set("behavior.start_minimized", self.start_minimized_cb.isChecked())
        config_service.set("behavior.close_to_tray", self.close_to_tray_cb.isChecked())
        state_service.set_preference("copy_auto_hide", self.copy_auto_hide_cb.isChecked())
        state_service.set_preference("copy_hide_delay_ms", self.copy_hide_delay_spin.value())
        state_service.set_preference("esc_hide_enabled", self.esc_hide_cb.isChecked())

        start_with_windows = self.start_with_windows_cb.isChecked()
        config_service.set("behavior.start_with_windows", start_with_windows)
        from app.services.autostart_service import autostart_service
        if not autostart_service.set_autostart(start_with_windows):
            logger.warning("Failed to apply autostart setting")

        config_service.set("storage.data_dir", self.data_dir_input.text())
        config_service.set("storage.export_dir", self.export_dir_input.text())
        config_service.set("storage.backup_dir", self.backup_dir_input.text())
        config_service.set("storage.log_dir", self.log_dir_input.text())

        config_service.set("behavior.hotkey", self.hotkey_input.text())
        config_service.set("behavior.main_hotkey", self.main_hotkey_input.text())
        state_service.set_preference("zoom_in_shortcut", self.zoom_in_shortcut_input.text() or "Ctrl+=")
        state_service.set_preference("zoom_out_shortcut", self.zoom_out_shortcut_input.text() or "Ctrl+-")
        state_service.set_preference("zoom_reset_shortcut", self.zoom_reset_shortcut_input.text() or "Ctrl+0")

        config_service.set("window.always_on_top", self.always_on_top_cb.isChecked())
        config_service.set("window.opacity", self.opacity_slider.value() / 100.0)
        config_service.set("window.remember_position", self.remember_position_cb.isChecked())
        config_service.set("window.remember_size", self.remember_size_cb.isChecked())

        config_service.set("backup.auto_backup_enabled", self.auto_backup_cb.isChecked())
        config_service.set("backup.auto_backup_interval_hours", self.backup_interval_spin.value())
        config_service.set("backup.max_backup_count", self.max_backup_spin.value())
        config_service.set("history.enabled", self.history_enabled_cb.isChecked())
        config_service.set("history.max_versions_per_file", self.max_versions_spin.value())

        config_service.set("features.template_variables", self.template_enabled_cb.isChecked())
        config_service.set("features.composer", self.composer_enabled_cb.isChecked())
        config_service.set("features.builtin_templates", self.builtin_templates_cb.isChecked())

        state_service.set_preference("search_enable_pinyin", self.search_enable_pinyin_cb.isChecked())
        state_service.set_preference("search_enable_initials", self.search_enable_initials_cb.isChecked())
        state_service.set_preference("search_enable_fuzzy", self.search_enable_fuzzy_cb.isChecked())
        state_service.set_preference("search_debounce_ms", self.search_debounce_spin.value())
        state_service.set_preference("search_max_results", self.search_max_results_spin.value())
        state_service.set_preference("search_fuzzy_mode", self.search_fuzzy_mode_combo.text())

        state_service.set_preference("semantic_search_enabled", self.semantic_search_enabled_cb.isChecked())
        state_service.set_preference("semantic_search_provider", self.semantic_search_provider_input.text())
        state_service.set_preference("semantic_search_api_base_url", self.semantic_search_api_url_input.text())
        state_service.set_preference("semantic_search_api_key", self.semantic_search_api_key_input.text())
        state_service.set_preference("semantic_search_api_model", self.semantic_search_api_model_input.text())
        state_service.set_preference("semantic_search_local_model", self.semantic_search_local_model_input.text())
        state_service.set_preference("semantic_search_top_k", self.semantic_search_top_k_spin.value())

        state_service.set_preference("ai_template_enabled", self.ai_template_enabled_cb.isChecked())
        state_service.set_preference("ai_template_provider", self.ai_template_provider_input.text())
        state_service.set_preference("ai_template_base_url", self.ai_template_base_url_input.text())
        state_service.set_preference("ai_template_api_key", self.ai_template_api_key_input.text())
        state_service.set_preference("ai_template_model", self.ai_template_model_input.text())
        state_service.set_preference("ai_template_temperature", self.ai_template_temperature_spin.value() / 10.0)
        state_service.set_preference("ai_template_detection_mode", self.ai_template_detection_mode_input.text())

        config_service.set("model.provider", self.model_provider_input.text())
        config_service.set("model.name", self.model_name_input.text())
        config_service.set("model.api_key", self.model_api_key_input.text())
        config_service.set("model.base_url", self.model_base_url_input.text())
        config_service.set("model.temperature", self.model_temperature_spin.value() / 10.0)

        self.accept()
