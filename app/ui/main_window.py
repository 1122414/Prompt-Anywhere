import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QThread, QTimer, QFileSystemWatcher, Signal
from PySide6.QtGui import QCloseEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
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
from app.services.search_service import SearchResult, search_service
from app.ui.dialogs import FolderDialog, PromptDialog
from app.ui.panels import EditorPanel
from app.ui.search_result_panel import SearchResultPanel
from app.ui.tray import TrayManager
from app.ui.tree_panel import TreePanel


class HotkeyThread(QThread):
    hotkey_pressed = Signal()

    def __init__(self, hotkey_str):
        super().__init__()
        self.hotkey_str = hotkey_str
        self._running = True

    def run(self):
        try:
            from pynput import keyboard

            def on_hotkey():
                if self._running:
                    self.hotkey_pressed.emit()

            hotkey = keyboard.GlobalHotKeys({
                self.hotkey_str: on_hotkey
            })
            hotkey.start()
            hotkey.join()
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Hotkey registration failed: {e}")

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

        self._always_on_top = config.always_on_top
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

        layout.addLayout(toolbar)

        self.splitter = QSplitter(Qt.Horizontal)

        self.tree_panel = TreePanel()
        self.tree_panel.setMinimumWidth(200)
        self.tree_panel.setMaximumWidth(350)
        self.tree_panel.prompt_selected.connect(self._on_prompt_selected)
        self.tree_panel.new_folder_requested.connect(self._on_new_folder)
        self.tree_panel.new_prompt_requested.connect(self._on_new_prompt)
        self.tree_panel.rename_folder_requested.connect(self._on_rename_folder)
        self.tree_panel.rename_prompt_requested.connect(self._on_rename_prompt)
        self.tree_panel.delete_folder_requested.connect(self._on_delete_folder)
        self.tree_panel.delete_prompt_requested.connect(self._on_delete_prompt_from_tree)
        self.tree_panel.tree.item_moved.connect(self._on_item_moved)
        self.splitter.addWidget(self.tree_panel)

        self.search_result_panel = SearchResultPanel()
        self.search_result_panel.setVisible(False)
        self.search_result_panel.result_selected.connect(self._on_search_result_selected)
        self.search_result_panel.result_copy_requested.connect(self._on_search_result_copy)
        self.search_result_panel.escape_pressed.connect(self._on_search_escape)
        self.splitter.addWidget(self.search_result_panel)

        self.editor_panel = EditorPanel()
        self.editor_panel.save_requested.connect(self._on_save)
        self.editor_panel.copy_requested.connect(self._on_copy)
        self.editor_panel.export_requested.connect(self._on_export)
        self.editor_panel.delete_requested.connect(self._on_delete_prompt)
        self.splitter.addWidget(self.editor_panel)

        self.splitter.setSizes([250, 650])
        layout.addWidget(self.splitter)

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

    def _setup_tray(self):
        self.tray = TrayManager(self)
        self.tray.toggle_window.connect(self.toggle_visibility)
        self.tray.new_prompt.connect(lambda: self._on_new_prompt(""))
        self.tray.open_data_dir.connect(self._open_data_dir)
        self.tray.quit_app.connect(self._quit_app)
        self.tray.show()

    def _setup_hotkey(self):
        try:
            hotkey_str = config.hotkey.lower()
            self.hotkey_thread = HotkeyThread(hotkey_str)
            self.hotkey_thread.hotkey_pressed.connect(self.toggle_visibility)
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
        if self.isVisible() and not self.isMinimized():
            self.hide()
        else:
            self.showNormal()
            self.activateWindow()
            self.raise_()
            self.search_input.setFocus()

    def _on_prompt_selected(self, prompt: PromptFile):
        if self.editor_panel.is_modified():
            result = self.editor_panel.check_unsaved()
            if result == AppConstants.CANCEL:
                return
            elif result == AppConstants.SAVE:
                self._on_save()
        self.editor_panel.load_prompt(prompt)

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
        self.search_result_panel.set_results(results, self._last_search_keyword)
        self._show_search_results()

    def _show_search_results(self):
        self.tree_panel.setVisible(False)
        self.search_result_panel.setVisible(True)
        self.search_result_panel.setFocus()
        if self.search_result_panel.list_widget.count() > 0:
            self.search_result_panel.select_first()

    def _hide_search_results(self):
        self.search_result_panel.setVisible(False)
        self.search_result_panel.clear_results()
        self.tree_panel.setVisible(True)

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
            if self.search_result_panel.isVisible():
                if event.key() == Qt.Key_Down:
                    self.search_result_panel.select_next()
                    return True
                elif event.key() == Qt.Key_Up:
                    self.search_result_panel.select_previous()
                    return True
                elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                    if event.modifiers() == Qt.ControlModifier:
                        result = self.search_result_panel.current_result()
                        if result:
                            self._on_search_result_copy(result)
                    else:
                        result = self.search_result_panel.current_result()
                        if result:
                            self._on_search_result_selected(result)
                    return True
                elif event.key() == Qt.Key_Escape:
                    if self.search_input.text():
                        self.search_input.clear()
                        return True
            if event.key() == Qt.Key_Escape and config.esc_hide_enabled:
                if self.search_input.text():
                    self.search_input.clear()
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
            self.file_watcher.removePaths(self.file_watcher.directories())
            if config.data_dir.exists():
                self.file_watcher.addPath(str(config.data_dir))
                for subdir in config.data_dir.rglob("*"):
                    if subdir.is_dir():
                        self.file_watcher.addPath(str(subdir))

    def _on_dir_changed(self, path: str):
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

        if self.hotkey_thread:
            self.hotkey_thread.stop()

        self.tray.hide()
        event.accept()
        QApplication.instance().quit()
