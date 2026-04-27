import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QThread
from PySide6.QtGui import QCloseEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from app.config import config
from app.constants import AppConstants, Messages
from app.services.clipboard_service import clipboard_service
from app.services.export_service import export_service
from app.services.file_service import PromptFile, file_service
from app.services.search_service import search_service
from app.ui.dialogs import CategoryDialog, PromptDialog
from app.ui.panels import CategoryPanel, EditorPanel, PromptListPanel
from app.ui.tray import TrayManager


class HotkeyThread(QThread):
    def __init__(self, hotkey_str, callback):
        super().__init__()
        self.hotkey_str = hotkey_str
        self.callback = callback
        self._running = True

    def run(self):
        try:
            from pynput import keyboard

            def on_hotkey():
                if self._running:
                    self.callback()

            hotkey = keyboard.GlobalHotKeys({
                self.hotkey_str: on_hotkey
            })
            hotkey.start()
            hotkey.join()
        except Exception:
            pass

    def stop(self):
        self._running = False
        self.quit()
        self.wait(1000)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(AppConstants.APP_NAME)
        self.setMinimumSize(600, 400)
        self.resize(config.window_width, config.window_height)
        self.move(config.window_x, config.window_y)

        self._last_category = "全部"
        self._setup_window_flags()
        self._setup_ui()
        self._setup_tray()
        self._setup_hotkey()
        self._setup_shortcuts()
        self._load_data()

    def _setup_window_flags(self):
        if config.always_on_top:
            self.setWindowFlag(Qt.WindowStaysOnTopHint, True)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(12, 8, 12, 8)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(Messages.SEARCH_PLACEHOLDER)
        self.search_input.textChanged.connect(self._on_search)
        search_layout.addWidget(self.search_input)

        self.new_prompt_btn = QPushButton("+ 新建")
        self.new_prompt_btn.clicked.connect(self._on_new_prompt)
        search_layout.addWidget(self.new_prompt_btn)
        layout.addLayout(search_layout)

        self.splitter = QSplitter(Qt.Horizontal)

        self.category_panel = CategoryPanel()
        self.category_panel.setMinimumWidth(120)
        self.category_panel.setMaximumWidth(200)
        self.category_panel.category_selected.connect(self._on_category_selected)
        self.category_panel.new_category_requested.connect(self._on_new_category)
        self.splitter.addWidget(self.category_panel)

        self.prompt_list_panel = PromptListPanel()
        self.prompt_list_panel.setMinimumWidth(180)
        self.prompt_list_panel.setMaximumWidth(300)
        self.prompt_list_panel.prompt_selected.connect(self._on_prompt_selected)
        self.prompt_list_panel.new_prompt_requested.connect(self._on_new_prompt)
        self.splitter.addWidget(self.prompt_list_panel)

        self.editor_panel = EditorPanel()
        self.editor_panel.save_requested.connect(self._on_save)
        self.editor_panel.copy_requested.connect(self._on_copy)
        self.editor_panel.export_requested.connect(self._on_export)
        self.editor_panel.delete_requested.connect(self._on_delete_prompt)
        self.splitter.addWidget(self.editor_panel)

        self.splitter.setSizes([150, 220, 530])
        layout.addWidget(self.splitter)

    def _setup_tray(self):
        self.tray = TrayManager(self)
        self.tray.toggle_window.connect(self.toggle_visibility)
        self.tray.new_prompt.connect(self._on_new_prompt)
        self.tray.open_data_dir.connect(self._open_data_dir)
        self.tray.quit_app.connect(self._quit_app)
        self.tray.show()

    def _setup_hotkey(self):
        try:
            hotkey_str = config.hotkey.lower().replace("+", "+")
            self.hotkey_thread = HotkeyThread(hotkey_str, self.toggle_visibility)
            self.hotkey_thread.start()
        except Exception:
            self.hotkey_thread = None

    def _setup_shortcuts(self):
        self.search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        self.search_shortcut.activated.connect(self.search_input.setFocus)

        self.save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        self.save_shortcut.activated.connect(self._on_save)

    def _load_data(self):
        self.category_panel.load_categories()
        self._load_prompts_for_current_category()

    def _load_prompts_for_current_category(self):
        category = self.category_panel.get_current_category()
        prompts = file_service.get_prompts(category)
        self.prompt_list_panel.load_prompts(prompts)

    def toggle_visibility(self):
        if self.isVisible() and not self.isMinimized():
            self.hide()
        else:
            self.showNormal()
            self.activateWindow()
            self.raise_()
            self.search_input.setFocus()

    def _on_category_selected(self, category: str):
        if self.editor_panel.is_modified():
            result = self.editor_panel.check_unsaved()
            if result == AppConstants.CANCEL:
                self.category_panel.select_category(self._last_category or "全部")
                return
            elif result == AppConstants.SAVE:
                self._on_save()
        self._last_category = category
        self._load_prompts_for_current_category()

    def _on_prompt_selected(self, prompt: PromptFile):
        if self.editor_panel.is_modified():
            result = self.editor_panel.check_unsaved()
            if result == AppConstants.CANCEL:
                return
            elif result == AppConstants.SAVE:
                self._on_save()
        self.editor_panel.load_prompt(prompt)

    def _on_search(self, text: str):
        category = self.category_panel.get_current_category()
        prompts = file_service.get_prompts(category)
        if text.strip():
            results = search_service.search(text, prompts, config.search_case_insensitive)
            self.prompt_list_panel.load_prompts(results)
        else:
            self.prompt_list_panel.load_prompts(prompts)

    def _on_new_category(self):
        dialog = CategoryDialog(self)
        if dialog.exec() == CategoryDialog.Accepted:
            name = dialog.get_name()
            if file_service.create_category(name):
                self.category_panel.load_categories()
                self.category_panel.select_category(name)

    def _on_new_prompt(self):
        categories = file_service.get_categories()
        if not categories:
            QMessageBox.information(self, "提示", "请先创建一个分类")
            return

        default_cat = self.category_panel.get_current_category()
        if default_cat == "全部":
            default_cat = categories[0] if categories else ""

        dialog = PromptDialog(self, categories, default_cat)
        if dialog.exec() == PromptDialog.Accepted:
            name = dialog.get_name()
            category = dialog.get_category()
            extension = dialog.get_extension()
            content = dialog.get_content()

            prompt = file_service.create_prompt(category, name, extension, content)
            if prompt:
                self.category_panel.load_categories()
                self.category_panel.select_category(category)
                self._load_prompts_for_current_category()
                self.prompt_list_panel.select_prompt(prompt)

    def _on_save(self):
        prompt = self.editor_panel.get_current_prompt()
        if prompt:
            content = self.editor_panel.get_content()
            if prompt.write_content(content):
                self.editor_panel.mark_saved()
                self.statusBar().showMessage(Messages.SAVED, 2000)

    def _on_copy(self):
        prompt = self.editor_panel.get_current_prompt()
        if prompt:
            content = prompt.read_content()
            if clipboard_service.copy_text(content):
                self.statusBar().showMessage(Messages.COPIED, 2000)

    def _on_export(self):
        prompt = self.editor_panel.get_current_prompt()
        if prompt:
            dest, _ = QFileDialog.getSaveFileName(
                self,
                "导出提示词",
                str(config.export_dir / f"{prompt.name}{prompt.extension}"),
                f"{prompt.extension.upper()} files (*{prompt.extension});;All files (*.*)"
            )
            if dest:
                if export_service.export(prompt, Path(dest)):
                    self.statusBar().showMessage(f"已导出到: {dest}", 3000)

    def _on_delete_prompt(self):
        prompt = self.editor_panel.get_current_prompt()
        if prompt:
            reply = QMessageBox.question(
                self,
                "确认删除",
                Messages.CONFIRM_DELETE_PROMPT.format(name=prompt.name),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                if file_service.delete_prompt(prompt):
                    self.editor_panel.load_prompt(None)
                    self._load_prompts_for_current_category()

    def _open_data_dir(self):
        try:
            if sys.platform == "win32":
                subprocess.run(["explorer", str(config.data_dir)])
            elif sys.platform == "darwin":
                subprocess.run(["open", str(config.data_dir)])
            else:
                subprocess.run(["xdg-open", str(config.data_dir)])
        except Exception:
            pass

    def _quit_app(self):
        self.close()

    def closeEvent(self, event: QCloseEvent):
        if self.editor_panel.is_modified():
            result = self.editor_panel.check_unsaved()
            if result == AppConstants.CANCEL:
                event.ignore()
                return
            elif result == AppConstants.SAVE:
                self._on_save()

        if self.hotkey_thread:
            self.hotkey_thread.stop()

        self.tray.hide()
        event.accept()
        QApplication.instance().quit()



