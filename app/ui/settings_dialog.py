import logging

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSlider,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt

from app.config import config

logger = logging.getLogger(__name__)


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumSize(600, 500)
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_general_tab(), "常规")
        self.tabs.addTab(self._create_paths_tab(), "路径")
        self.tabs.addTab(self._create_hotkeys_tab(), "快捷键")
        self.tabs.addTab(self._create_window_tab(), "窗口")
        self.tabs.addTab(self._create_data_safety_tab(), "数据安全")
        self.tabs.addTab(self._create_features_tab(), "功能开关")
        self.tabs.addTab(self._create_search_tab(), "搜索设置")
        self.tabs.addTab(self._create_semantic_search_tab(), "语义搜索")
        self.tabs.addTab(self._create_ai_template_tab(), "AI模板助手")
        self.tabs.addTab(self._create_about_tab(), "关于")

        layout.addWidget(self.tabs)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _create_general_tab(self):
        tab = QWidget()
        layout = QFormLayout(tab)

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

        return tab

    def _create_paths_tab(self):
        tab = QWidget()
        layout = QFormLayout(tab)

        data_layout = QHBoxLayout()
        self.data_dir_input = QLineEdit()
        self.data_dir_input.setPlaceholderText("./data")
        data_layout.addWidget(self.data_dir_input)
        data_browse = QPushButton("浏览")
        data_browse.clicked.connect(
            lambda: self._browse_dir(self.data_dir_input)
        )
        data_layout.addWidget(data_browse)
        layout.addRow("数据目录:", data_layout)

        export_layout = QHBoxLayout()
        self.export_dir_input = QLineEdit()
        self.export_dir_input.setPlaceholderText("./exports")
        export_layout.addWidget(self.export_dir_input)
        export_browse = QPushButton("浏览")
        export_browse.clicked.connect(
            lambda: self._browse_dir(self.export_dir_input)
        )
        export_layout.addWidget(export_browse)
        layout.addRow("导出目录:", export_layout)

        backup_layout = QHBoxLayout()
        self.backup_dir_input = QLineEdit()
        self.backup_dir_input.setPlaceholderText("./backups")
        backup_layout.addWidget(self.backup_dir_input)
        backup_browse = QPushButton("浏览")
        backup_browse.clicked.connect(
            lambda: self._browse_dir(self.backup_dir_input)
        )
        backup_layout.addWidget(backup_browse)
        layout.addRow("备份目录:", backup_layout)

        log_layout = QHBoxLayout()
        self.log_dir_input = QLineEdit()
        self.log_dir_input.setPlaceholderText("./logs")
        log_layout.addWidget(self.log_dir_input)
        log_browse = QPushButton("浏览")
        log_browse.clicked.connect(
            lambda: self._browse_dir(self.log_dir_input)
        )
        log_layout.addWidget(log_browse)
        layout.addRow("日志目录:", log_layout)

        return tab

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
        hint_label.setStyleSheet("color: #888;")
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

        return tab

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

        return tab

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

        self.start_minimized_cb.setChecked(
            config_service.get("behavior.start_minimized", False)
        )
        self.close_to_tray_cb.setChecked(
            config_service.get("behavior.close_to_tray", True)
        )
        self.copy_auto_hide_cb.setChecked(config.copy_auto_hide)
        self.copy_hide_delay_spin.setValue(config.copy_hide_delay_ms)
        self.esc_hide_cb.setChecked(config.esc_hide_enabled)

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

        self.always_on_top_cb.setChecked(config.always_on_top)
        self.opacity_slider.setValue(int(config.default_window_opacity * 100))
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

    def _on_accept(self):
        from app.services.config_service import config_service
        from app.services.state_service import state_service

        config_service.set("behavior.start_minimized", self.start_minimized_cb.isChecked())
        config_service.set("behavior.close_to_tray", self.close_to_tray_cb.isChecked())
        state_service.set_preference("copy_auto_hide", self.copy_auto_hide_cb.isChecked())
        state_service.set_preference("copy_hide_delay_ms", self.copy_hide_delay_spin.value())
        state_service.set_preference("esc_hide_enabled", self.esc_hide_cb.isChecked())

        config_service.set("storage.data_dir", self.data_dir_input.text())
        config_service.set("storage.export_dir", self.export_dir_input.text())
        config_service.set("storage.backup_dir", self.backup_dir_input.text())
        config_service.set("storage.log_dir", self.log_dir_input.text())

        config_service.set("behavior.hotkey", self.hotkey_input.text())
        config_service.set("behavior.main_hotkey", self.main_hotkey_input.text())

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

        self.accept()
