import logging
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

from PySide6.QtCore import Qt, QThread, QTimer, QFileSystemWatcher, Signal
from PySide6.QtGui import QCloseEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSlider,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from app.config import config
from app.constants import AppConstants, Messages
from app.services.clipboard_service import clipboard_service
from app.services.export_service import export_service
from app.services.file_service import PromptFile, file_service
from app.services.search_service import SearchResult, search_service
from app.services.state_service import state_service
from app.services.startup_service import startup_service
from app.services.logging_service import logging_service
from app.ui.dialogs import FolderDialog, PromptDialog
from app.ui.panels import EditorPanel
from app.ui.search_popup import SearchPopupWindow
from app.ui.tray import TrayManager
from app.ui.tree_panel import TreePanel


class HotkeyThread(QThread):
    hotkey_pressed = Signal()

    def __init__(self, hotkey_str):
        super().__init__()
        self.hotkey_str = hotkey_str
        self._running = True
        self._hotkey = None

    def run(self):
        try:
            from pynput import keyboard

            def on_hotkey():
                if self._running:
                    self.hotkey_pressed.emit()

            self._hotkey = keyboard.GlobalHotKeys({
                self.hotkey_str: on_hotkey
            })
            self._hotkey.start()
            while self._running:
                self.msleep(100)
            self._hotkey.stop()
        except Exception as e:
            logger.warning(f"Hotkey registration failed: {e}")

    def stop(self):
        self._running = False
        self.wait(2000)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(config.app_name)
        self.setMinimumSize(600, 400)

        window_state = state_service.get_window_state()
        width = window_state.get("width", config.default_window_width)
        height = window_state.get("height", config.default_window_height)
        x = window_state.get("x", 100)
        y = window_state.get("y", 100)
        self.resize(width, height)
        self.move(x, y)

        self._always_on_top = window_state.get("always_on_top", config.always_on_top)
        self._window_opacity = window_state.get("opacity", config.default_window_opacity)
        self.setWindowOpacity(self._window_opacity)

        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._do_search)
        self._search_worker = None
        self._last_search_keyword = ""

        self._setup_window_flags()
        self._setup_ui()
        self._setup_tray()
        self._setup_hotkey()
        self._setup_shortcuts()
        self._setup_file_watcher()
        self._load_data()

        search_service.rebuild_index()

        last_category = state_service.get_last_selected_category()
        if last_category:
            self.tree_panel.select_category(last_category)

        last_file = state_service.get_last_selected_file()
        if last_file:
            full_path = config.data_dir / last_file
            if full_path.exists():
                self._on_prompt_selected(PromptFile(full_path))

        last_mode = state_service.get_last_view_mode()
        if last_mode:
            self.editor_panel.set_mode(last_mode)

    def _setup_window_flags(self):
        if self._always_on_top:
            self.setWindowFlag(Qt.WindowStaysOnTopHint, True)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(12, 8, 12, 8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(Messages.SEARCH_PLACEHOLDER)
        self.search_input.textChanged.connect(self._on_search)
        self.search_input.installEventFilter(self)
        toolbar.addWidget(self.search_input)

        self.pin_btn = QPushButton("📌 置顶" if self._always_on_top else "置顶")
        self.pin_btn.setCheckable(True)
        self.pin_btn.setChecked(self._always_on_top)
        self.pin_btn.clicked.connect(self._toggle_always_on_top)
        toolbar.addWidget(self.pin_btn)

        self.import_menu = QMenu(self)
        self.import_menu.addAction("导入文件", self._on_import_file)
        self.import_menu.addAction("导入文件夹", self._on_import_folder)

        self.import_btn = QPushButton("导入 ▾")
        self.import_btn.setMenu(self.import_menu)
        toolbar.addWidget(self.import_btn)

        self.template_menu = QMenu(self)
        if config.show_template_button:
            self.template_menu.addAction("使用模板", self._on_use_template_from_toolbar)
        self.template_menu.addAction("保存为模板", self._on_save_as_template)
        if config.enable_builtin_templates:
            self.template_menu.addAction("导入内置模板", self._on_import_builtin)

        self.template_btn = QPushButton("模板 ▾")
        self.template_btn.setMenu(self.template_menu)
        toolbar.addWidget(self.template_btn)

        if config.show_composer_button:
            self.composer_btn = QPushButton("组合器")
            self.composer_btn.clicked.connect(self._on_open_composer)
            toolbar.addWidget(self.composer_btn)

        toolbar.addWidget(QLabel("透明度:"))
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setMinimum(int(config.min_window_opacity * 100))
        self.opacity_slider.setMaximum(int(config.max_window_opacity * 100))
        self.opacity_slider.setValue(int(self._window_opacity * 100))
        self.opacity_slider.setFixedWidth(100)
        self.opacity_slider.valueChanged.connect(self._on_opacity_changed)
        toolbar.addWidget(self.opacity_slider)

        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setFixedWidth(30)
        self.settings_btn.setToolTip("设置")
        self.settings_btn.clicked.connect(self._on_settings)
        toolbar.addWidget(self.settings_btn)

        layout.addLayout(toolbar)

        self.splitter = QSplitter(Qt.Horizontal)

        self.tree_panel = TreePanel()
        self.tree_panel.setMinimumWidth(220)
        self.tree_panel.setMaximumWidth(400)
        self.tree_panel.prompt_selected.connect(self._on_prompt_selected)
        self.tree_panel.new_folder_requested.connect(self._on_new_folder)
        self.tree_panel.new_prompt_requested.connect(self._on_new_prompt)
        self.tree_panel.rename_folder_requested.connect(self._on_rename_folder)
        self.tree_panel.rename_prompt_requested.connect(self._on_rename_prompt)
        self.tree_panel.delete_folder_requested.connect(self._on_delete_folder)
        self.tree_panel.delete_prompt_requested.connect(self._on_delete_prompt_from_tree)
        self.tree_panel.tree.item_moved.connect(self._on_item_moved)
        self.splitter.addWidget(self.tree_panel)

        self.editor_panel = EditorPanel()
        self.editor_panel.save_requested.connect(self._on_save)
        self.editor_panel.copy_requested.connect(self._on_copy)
        self.editor_panel.export_requested.connect(self._on_export)
        self.editor_panel.delete_requested.connect(self._on_delete_prompt)
        self.splitter.addWidget(self.editor_panel)

        self.splitter.setSizes([280, 620])
        layout.addWidget(self.splitter)

        self.search_popup = SearchPopupWindow(self)
        self.search_popup.result_selected.connect(self._on_search_result_selected)
        self.search_popup.result_copy_requested.connect(self._on_search_result_copy)
        self.search_popup.escape_pressed.connect(self._on_search_escape)

    def _toggle_always_on_top(self):
        self._always_on_top = not self._always_on_top
        self.setWindowFlag(Qt.WindowStaysOnTopHint, self._always_on_top)
        self.show()
        if self._always_on_top:
            self.pin_btn.setText("📌 置顶")
            self.pin_btn.setChecked(True)
        else:
            self.pin_btn.setText("置顶")
            self.pin_btn.setChecked(False)

    def _on_import_file(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "导入提示词文件",
            "",
            f"提示词文件 ({' *.'.join(config.supported_prompt_extensions)});;所有文件 (*.*)",
        )
        if not files:
            return
        category = self._select_import_category()
        if not category:
            return
        imported = 0
        for file_path in files:
            src = Path(file_path)
            success, msg = file_service.import_file(src, category, "rename")
            if success:
                imported += 1
                search_service.update_index_file(msg)
                self.tree_panel.add_prompt_item(category, PromptFile(config.data_dir / msg))
            else:
                logger.warning(f"Import failed: {msg}")
        if imported > 0:
            self.statusBar().showMessage(f"成功导入 {imported} 个文件", 3000)

    def _on_import_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "导入文件夹")
        if not folder:
            return
        category = self._select_import_category()
        if not category:
            return
        count, errors = file_service.import_folder(Path(folder), category, "rename")
        if count > 0:
            search_service.rebuild_index()
            self.tree_panel.load_tree()
            self.statusBar().showMessage(f"成功导入 {count} 个文件", 3000)
        if errors:
            logger.warning(f"Import errors: {errors}")

    def _on_import_builtin(self):
        from app.ui.dialogs import BuiltinTemplateDialog
        dialog = BuiltinTemplateDialog(self)
        if dialog.exec() == BuiltinTemplateDialog.Accepted:
            self.tree_panel.load_tree()
            search_service.rebuild_index()

    def _on_open_composer(self):
        from app.ui.composer_dialog import ComposerDialog
        dialog = ComposerDialog(self)
        dialog.exec()
        self.tree_panel.load_tree()
        search_service.rebuild_index()

    def _on_use_template_from_toolbar(self):
        prompt = self.editor_panel.get_current_prompt()
        if not prompt:
            QMessageBox.information(self, "提示", "请先打开一个提示词文件")
            return
        self.editor_panel._on_use_template()

    def _on_save_as_template(self):
        prompt = self.editor_panel.get_current_prompt()
        if not prompt:
            QMessageBox.information(self, "提示", "请先打开一个提示词文件")
            return
        content = self.editor_panel.get_content()
        if not content.strip():
            QMessageBox.warning(self, "提示", "当前内容为空，无法保存为模板")
            return

        from PySide6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "保存为模板", "模板名称：", text=prompt.name)
        if not ok or not name:
            return

        template_dir = config.data_dir / "我的模板"
        template_dir.mkdir(parents=True, exist_ok=True)
        template_path = template_dir / f"{name}.md"
        if template_path.exists():
            reply = QMessageBox.question(
                self, "确认覆盖",
                f"模板 '{name}' 已存在，是否覆盖？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return

        template_path.write_text(content, encoding=config.file_encoding)
        search_service.update_index_file(f"我的模板/{name}.md")
        QMessageBox.information(self, "保存成功", f"模板已保存到：我的模板/{name}.md")

    def _select_import_category(self) -> str:
        from PySide6.QtWidgets import QInputDialog
        categories = file_service.get_categories()
        if not categories:
            return ""
        category, ok = QInputDialog.getItem(
            self, "选择分类", "导入到分类:", categories, 0, False
        )
        if ok and category:
            return category
        return ""

    def _on_opacity_changed(self, value: int):
        opacity = value / 100.0
        self._window_opacity = opacity
        self.setWindowOpacity(opacity)

    def _on_settings(self):
        from app.ui.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self)
        if dialog.exec() == SettingsDialog.Accepted:
            self.statusBar().showMessage("设置已保存", 2000)
            self.tree_panel.load_tree()

    def _setup_tray(self):
        self.tray = TrayManager(self)
        self.tray.open_main_window.connect(self.show_main)
        self.tray.toggle_quick_window.connect(self.toggle_quick)
        self.tray.new_prompt.connect(lambda: self._on_new_prompt(""))
        self.tray.open_data_dir.connect(self._open_data_dir)
        self.tray.quit_app.connect(self._force_quit)
        self.tray.show()

    def _setup_hotkey(self):
        try:
            hotkey_str = config.hotkey.lower()
            self.hotkey_thread = HotkeyThread(hotkey_str)
            self.hotkey_thread.hotkey_pressed.connect(self.toggle_quick)
            self.hotkey_thread.start()
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to setup hotkey: {e}")
            self.hotkey_thread = None

    def _setup_shortcuts(self):
        self.search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        self.search_shortcut.activated.connect(self.search_input.setFocus)

        self.save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        self.save_shortcut.activated.connect(self._on_save)

    def _load_data(self):
        self.tree_panel.load_tree()

    def toggle_visibility(self):
        self.toggle_quick()

    def show_main(self):
        self.showNormal()
        self.activateWindow()
        self.raise_()
        self.search_input.setFocus()

    def toggle_quick(self):
        if hasattr(self, "quick_window") and self.quick_window:
            self.quick_window.toggle_visibility()

    def _on_prompt_selected(self, prompt: PromptFile):
        if self.editor_panel.is_modified():
            result = self.editor_panel.check_unsaved()
            if result == AppConstants.CANCEL:
                return
            elif result == AppConstants.SAVE:
                self._on_save()
        self.editor_panel.load_prompt(prompt)
        if prompt:
            rel = prompt.path.relative_to(config.data_dir).as_posix()
            state_service.set_last_selected_file(rel)
            state_service.add_recent_file(rel)

    def _on_item_moved(self, source_path: str, target_path: str):
        current = self.editor_panel.get_current_prompt()
        if not current:
            return
        current_rel = str(current.path.relative_to(config.data_dir)).replace("\\", "/")
        new_rel = None
        if current_rel == source_path:
            new_rel = (Path(target_path) / Path(source_path).name).as_posix()
        elif current_rel.startswith(source_path + "/"):
            new_rel = (Path(target_path) / Path(source_path).name / current_rel[len(source_path) + 1:]).as_posix()
        if new_rel:
            new_path = config.data_dir / new_rel
            if new_path.exists():
                if not self.editor_panel.load_prompt(PromptFile(new_path)):
                    self.editor_panel.update_prompt_path(PromptFile(new_path))

    def _on_search(self, text: str):
        self._last_search_keyword = text.strip()
        self._search_timer.stop()
        if not self._last_search_keyword:
            self._hide_search_results()
            return
        self._search_timer.start(config.search_debounce_ms)

    def _do_search(self):
        keyword = self._last_search_keyword
        if not keyword:
            self._hide_search_results()
            return
        search_id, worker = search_service.search_async(keyword, config.search_case_insensitive)
        worker.results_ready.connect(self._on_search_results_ready)
        worker.start()
        self._search_worker = worker

    def _on_search_results_ready(self, search_id: int, results: list[SearchResult]):
        if search_id != search_service.get_current_search_id():
            return
        if not self._last_search_keyword:
            self._hide_search_results()
            return
        self.search_popup.show_results(results, self._last_search_keyword)

    def _show_search_results(self):
        pass

    def _hide_search_results(self):
        self.search_popup.clear()

    def _on_search_result_selected(self, result: SearchResult):
        full_path = config.data_dir / result.path
        if full_path.exists():
            prompt = PromptFile(full_path)
            self._on_prompt_selected(prompt)
            self.search_input.clear()
            self._hide_search_results()

    def _on_search_result_copy(self, result: SearchResult):
        full_path = config.data_dir / result.path
        if full_path.exists():
            prompt = PromptFile(full_path)
            content = prompt.read_content()
            if clipboard_service.copy_text(content):
                self.statusBar().showMessage(Messages.COPIED, 2000)
                state_service.add_recent_file(result.path)
                self._on_copy_done()

    def _on_search_escape(self):
        self.search_input.clear()
        self._hide_search_results()

    def _on_copy_done(self):
        if config.copy_auto_hide:
            QTimer.singleShot(config.copy_hide_delay_ms, self.hide)

    def _on_new_folder(self, parent_path: str):
        dialog = FolderDialog(self, folder_path=parent_path)
        if dialog.exec() == FolderDialog.Accepted:
            name = dialog.get_name()
            target = file_service._resolve_path(parent_path) / name
            if target.exists():
                QMessageBox.warning(self, "错误", f'文件夹"{name}"已存在')
                return
            if file_service.create_folder(parent_path, name):
                search_service.rebuild_index()
                self.tree_panel.add_folder_item(parent_path, name)

    def _on_new_prompt(self, parent_path: str):
        dialog = PromptDialog(self, parent_path=parent_path)
        if dialog.exec() == PromptDialog.Accepted:
            name = dialog.get_name()
            extension = dialog.get_extension()
            content = dialog.get_content()
            prompt = file_service.create_prompt(parent_path, name, extension, content)
            if prompt:
                rel = prompt.path.relative_to(config.data_dir).as_posix()
                search_service.update_index_file(rel)
                self.tree_panel.add_prompt_item(parent_path, prompt)
            else:
                QMessageBox.warning(self, "创建失败", f'已存在同名文件"{name}{extension}"')

    def _on_save(self):
        prompt = self.editor_panel.get_current_prompt()
        if prompt:
            content = self.editor_panel.get_content()
            if prompt.write_content(content):
                self.editor_panel.mark_saved()
                self.statusBar().showMessage(Messages.SAVED, 2000)
                rel = prompt.path.relative_to(config.data_dir).as_posix()
                search_service.update_index_file(rel)

    def _on_copy(self):
        prompt = self.editor_panel.get_current_prompt()
        if prompt:
            content = prompt.read_content()
            if clipboard_service.copy_text(content):
                self.statusBar().showMessage(Messages.COPIED, 2000)
                rel = prompt.path.relative_to(config.data_dir).as_posix()
                state_service.add_recent_file(rel)
                self._on_copy_done()

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
                    rel = prompt.path.relative_to(config.data_dir).as_posix()
                    state_service.add_recent_file(rel)

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
                rel = prompt.path.relative_to(config.data_dir).as_posix()
                if file_service.delete_prompt(prompt):
                    search_service.remove_index_file(rel)
                    self.editor_panel.load_prompt(None)
                    self.tree_panel.remove_prompt_item(prompt)

    def _open_data_dir(self):
        try:
            if sys.platform == "win32":
                subprocess.run(["explorer", str(config.data_dir)])
            elif sys.platform == "darwin":
                subprocess.run(["open", str(config.data_dir)])
            else:
                subprocess.run(["xdg-open", str(config.data_dir)])
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to open data dir: {e}")

    def _on_rename_folder(self, folder_path: str):
        from PySide6.QtWidgets import QInputDialog
        old_name = Path(folder_path).name
        new_name, ok = QInputDialog.getText(
            self, "重命名文件夹", "新名称:", text=old_name
        )
        if ok and new_name and new_name != old_name:
            if not file_service.rename_folder(folder_path, new_name):
                QMessageBox.warning(self, "错误", f'文件夹"{new_name}"已存在')
                return
            new_path = str(Path(folder_path).parent / new_name).replace("\\", "/")
            if new_path.startswith("./"):
                new_path = new_path[2:]
            config.rename_folder_icons(folder_path, new_path)
            self.tree_panel.rename_folder_item(folder_path, new_name)

    def _on_delete_folder(self, folder_path: str):
        reply = QMessageBox.question(
            self,
            "确认删除",
            f'确定要删除文件夹"{Path(folder_path).name}"吗？\n该文件夹下的所有内容将被删除。',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            current = self.editor_panel.get_current_prompt()
            if current:
                current_path = current.rel_path.as_posix()
                if current_path == folder_path or current_path.startswith(folder_path + "/"):
                    self.editor_panel.load_prompt(None)
            if file_service.delete_folder(folder_path):
                search_service.rebuild_index()
                self.tree_panel.remove_folder_item(folder_path)

    def _on_rename_prompt(self, prompt: PromptFile):
        from PySide6.QtWidgets import QInputDialog
        new_name, ok = QInputDialog.getText(
            self, "重命名提示词", "新名称:", text=prompt.name
        )
        if ok and new_name and new_name != prompt.name:
            old_rel = prompt.path.relative_to(config.data_dir).as_posix()
            if not file_service.rename_prompt(prompt, new_name):
                QMessageBox.warning(self, "错误", f'文件"{new_name}{prompt.extension}"已存在')
                return
            search_service.rebuild_index()
            self.tree_panel.rename_prompt_item(prompt, new_name)

    def _on_delete_prompt_from_tree(self, prompt: PromptFile):
        reply = QMessageBox.question(
            self,
            "确认删除",
            Messages.CONFIRM_DELETE_PROMPT.format(name=prompt.name),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            current = self.editor_panel.get_current_prompt()
            if current and current.path == prompt.path:
                self.editor_panel.load_prompt(None)
            rel = prompt.path.relative_to(config.data_dir).as_posix()
            if file_service.delete_prompt(prompt):
                search_service.remove_index_file(rel)
                self.tree_panel.remove_prompt_item(prompt)

    def _setup_file_watcher(self):
        if config.enable_file_watcher:
            self.file_watcher = QFileSystemWatcher(self)
            self.file_watcher.directoryChanged.connect(self._on_dir_changed)
            self._update_watched_dirs()

    def eventFilter(self, obj, event):
        if obj == self.search_input and event.type() == event.Type.KeyPress:
            if self.search_popup.isVisible():
                if event.key() == Qt.Key_Down:
                    self.search_popup.panel.select_next()
                    return True
                elif event.key() == Qt.Key_Up:
                    self.search_popup.panel.select_previous()
                    return True
                elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                    if event.modifiers() == Qt.ControlModifier:
                        result = self.search_popup.panel.current_result()
                        if result:
                            self._on_search_result_copy(result)
                    else:
                        result = self.search_popup.panel.current_result()
                        if result:
                            self._on_search_result_selected(result)
                    return True
                elif event.key() == Qt.Key_Escape:
                    if self.search_input.text():
                        self.search_input.clear()
                        self._hide_search_results()
                        return True
            if event.key() == Qt.Key_Escape and config.esc_hide_enabled:
                if self.search_input.text():
                    self.search_input.clear()
                    self._hide_search_results()
                    return True
                if self.editor_panel.is_modified():
                    result = self.editor_panel.check_unsaved()
                    if result == AppConstants.CANCEL:
                        return True
                    elif result == AppConstants.SAVE:
                        self._on_save()
                self.hide()
                return True
        return super().eventFilter(obj, event)

    def _update_watched_dirs(self):
        if hasattr(self, "file_watcher"):
            dirs = self.file_watcher.directories()
            if dirs:
                self.file_watcher.removePaths(dirs)
            if config.data_dir.exists():
                self.file_watcher.addPath(str(config.data_dir))
                for subdir in config.data_dir.rglob("*"):
                    if subdir.is_dir():
                        self.file_watcher.addPath(str(subdir))

    def _on_dir_changed(self, path: str):
        if getattr(self, "_skip_watcher", False):
            return
        search_service.rebuild_index()
        self.tree_panel.load_tree()
        self._update_watched_dirs()

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

        self._save_window_state()
        event.ignore()

        if state_service.get_preference("close_behavior_set", False):
            behavior = state_service.get_preference("close_behavior", "minimize")
            if behavior == "quit":
                self._force_quit()
                return
        else:
            self._show_close_dialog()

        self.hide()

    def _show_close_dialog(self):
        from PySide6.QtWidgets import QCheckBox, QDialog, QLabel, QPushButton, QVBoxLayout
        dialog = QDialog(self)
        dialog.setWindowTitle("关闭提示")
        dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowStaysOnTopHint)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("点击关闭按钮，您希望："))
        btn_layout = QHBoxLayout()
        minimize_btn = QPushButton("最小化到托盘")
        quit_btn = QPushButton("退出程序")
        btn_layout.addWidget(minimize_btn)
        btn_layout.addWidget(quit_btn)
        layout.addLayout(btn_layout)
        no_show_cb = QCheckBox("不再显示此提示")
        layout.addWidget(no_show_cb)

        result = {"action": None}

        def on_minimize():
            result["action"] = "minimize"
            dialog.accept()

        def on_quit():
            result["action"] = "quit"
            dialog.accept()

        minimize_btn.clicked.connect(on_minimize)
        quit_btn.clicked.connect(on_quit)
        dialog.exec()

        if result["action"] is None:
            self.hide()
            return

        if no_show_cb.isChecked():
            state_service.set_preference("close_behavior_set", True)
            state_service.set_preference("close_behavior", result["action"])

        if result["action"] == "quit":
            self._force_quit()
        else:
            self.hide()

    def _force_quit(self):
        if self.hotkey_thread:
            self.hotkey_thread.stop()
        self.tray.hide()
        self._save_window_state()
        QApplication.instance().quit()

    def _save_window_state(self):
        pos = self.pos()
        size = self.size()
        state_service.set_window_state(
            x=pos.x(),
            y=pos.y(),
            width=size.width(),
            height=size.height(),
            opacity=self._window_opacity,
            always_on_top=self._always_on_top,
        )
