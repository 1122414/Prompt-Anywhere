import shutil
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.config import config
from app.services.file_service import PromptFile, file_service
from app.services.search_service import search_service
from app.services.state_service import state_service

_ICON_KEYS = [
    "SP_DirIcon",
    "SP_DirOpenIcon",
    "SP_DriveHDIcon",
    "SP_DriveCDIcon",
    "SP_ComputerIcon",
    "SP_DesktopIcon",
    "SP_TrashIcon",
    "SP_NetworkIcon",
]


class DraggableTreeWidget(QTreeWidget):
    item_moved = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QTreeWidget.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setDropIndicatorShown(True)
        self.setSelectionMode(QTreeWidget.ExtendedSelection)

    def _get_item_path(self, item):
        if not item:
            return ""
        parts = []
        while item:
            text = item.text(0)
            if text != "全部":
                parts.insert(0, text)
            item = item.parent()
        return "/".join(parts)

    def _is_folder_item(self, item):
        if not item:
            return False
        return item.data(0, Qt.UserRole + 1) == "folder"

    def dropEvent(self, event):
        target = self.itemAt(event.position().toPoint())
        if not target or not self._is_folder_item(target):
            event.ignore()
            return

        dragged_items = self.selectedItems()
        if not dragged_items:
            event.ignore()
            return

        dragged = dragged_items[0]
        if dragged == target:
            event.ignore()
            return

        source_path = self._get_item_path(dragged)
        target_path = self._get_item_path(target)
        is_target_root = target.text(0) == "全部"

        if not source_path:
            event.ignore()
            return
        if not target_path and not is_target_root:
            event.ignore()
            return

        if source_path == target_path or target_path.startswith(source_path + "/"):
            event.ignore()
            return

        if self._is_folder_item(dragged):
            if source_path.startswith(target_path + "/"):
                event.ignore()
                return
            dest = Path(config.data_dir) / target_path / Path(source_path).name
            if dest.exists():
                QMessageBox.warning(self, "错误", f'目标文件夹中已存在同名文件夹"{Path(source_path).name}"')
                event.ignore()
                return
            try:
                shutil.move(str(Path(config.data_dir) / source_path), str(dest))
                new_rel = str(dest.relative_to(config.data_dir)).replace("\\", "/")
                config.rename_folder_icons(source_path, new_rel)
            except Exception as e:
                QMessageBox.warning(self, "错误", f"移动失败: {e}")
                event.ignore()
                return
        else:
            data = dragged.data(0, Qt.UserRole)
            if isinstance(data, PromptFile):
                source_parent = str(data.path.parent.relative_to(config.data_dir)).replace("\\", "/")
                if source_parent == target_path:
                    event.ignore()
                    return
                dest = Path(config.data_dir) / target_path / data.path.name
                if dest.exists():
                    QMessageBox.warning(self, "错误", f'目标文件夹中已存在同名文件"{data.path.name}"')
                    event.ignore()
                    return
                try:
                    shutil.move(str(data.path), str(dest))
                except Exception as e:
                    QMessageBox.warning(self, "错误", f"移动失败: {e}")
                    event.ignore()
                    return

        if self._is_folder_item(dragged):
            old_parent = dragged.parent()
            if old_parent:
                old_parent.removeChild(dragged)
            else:
                index = self.indexOfTopLevelItem(dragged)
                self.takeTopLevelItem(index)
            target.addChild(dragged)
            self._update_folder_paths(dragged, new_rel)
        else:
            data = dragged.data(0, Qt.UserRole)
            if isinstance(data, PromptFile):
                old_parent = dragged.parent()
                if old_parent:
                    old_parent.removeChild(dragged)
                else:
                    index = self.indexOfTopLevelItem(dragged)
                    self.takeTopLevelItem(index)
                target.addChild(dragged)
                data.path = dest
                data.name = dest.stem
                dragged.setData(0, Qt.UserRole, data)

        self.item_moved.emit(source_path, target_path)
        event.accept()

    def _update_folder_paths(self, item, new_path):
        item.setIcon(0, self.parent()._folder_icon(new_path))
        for i in range(item.childCount()):
            child = item.child(i)
            child_path = self.parent()._get_item_path(child)
            if self.parent()._is_folder_item(child):
                self._update_folder_paths(child, child_path)
            else:
                data = child.data(0, Qt.UserRole)
                if isinstance(data, PromptFile):
                    data.rel_path = data.path.relative_to(config.data_dir)
                    child.setData(0, Qt.UserRole, data)


class TreePanel(QWidget):
    prompt_selected = Signal(object)
    new_folder_requested = Signal(str)
    new_prompt_requested = Signal(str)
    rename_folder_requested = Signal(str)
    rename_prompt_requested = Signal(object)
    delete_folder_requested = Signal(str)
    delete_prompt_requested = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        header = QHBoxLayout()
        header_label = QLabel("目录")
        header_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header.addWidget(header_label)
        header.addStretch()

        self.new_folder_btn = QPushButton("+ 文件夹")
        self.new_folder_btn.setToolTip("新建文件夹")
        self.new_folder_btn.clicked.connect(self._on_new_folder)
        header.addWidget(self.new_folder_btn)

        self.new_prompt_btn = QPushButton("+ 文件")
        self.new_prompt_btn.setToolTip("新建提示词文件")
        self.new_prompt_btn.clicked.connect(self._on_new_prompt)
        header.addWidget(self.new_prompt_btn)

        layout.addLayout(header)

        self.tree = DraggableTreeWidget(self)
        self.tree.setHeaderHidden(True)
        self.tree.setFrameShape(QTreeWidget.NoFrame)
        self.tree.itemClicked.connect(self._on_item_clicked)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.tree)

        batch = QHBoxLayout()
        self.batch_move_btn = QPushButton("批量移动")
        self.batch_move_btn.clicked.connect(self._on_batch_move)
        batch.addWidget(self.batch_move_btn)

        self.batch_delete_btn = QPushButton("批量删除")
        self.batch_delete_btn.clicked.connect(self._on_batch_delete)
        batch.addWidget(self.batch_delete_btn)

        self.batch_export_btn = QPushButton("批量导出")
        self.batch_export_btn.clicked.connect(self._on_batch_export)
        batch.addWidget(self.batch_export_btn)

        self.open_folder_btn = QPushButton("打开文件夹")
        self.open_folder_btn.clicked.connect(self._on_open_containing_folder)
        batch.addWidget(self.open_folder_btn)

        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.clicked.connect(self.tree.selectAll)
        batch.addWidget(self.select_all_btn)

        layout.addLayout(batch)

    def _folder_icon(self, folder_path):
        icon_key = config.folder_icon(folder_path)
        if icon_key and hasattr(self.style().StandardPixmap, icon_key):
            return self.style().standardIcon(getattr(self.style().StandardPixmap, icon_key))
        return self.style().standardIcon(self.style().StandardPixmap.SP_DirIcon)

    def _on_new_folder(self):
        current = self.tree.currentItem()
        path = self._get_item_path(current) if current else ""
        if path and not self._is_folder_item(current):
            parent = Path(path).parent
            path = "" if parent == Path(".") else str(parent)
        self.new_folder_requested.emit(path)

    def _on_new_prompt(self):
        current = self.tree.currentItem()
        path = self._get_item_path(current) if current else ""
        if path and not self._is_folder_item(current):
            parent = Path(path).parent
            path = "" if parent == Path(".") else str(parent)
        self.new_prompt_requested.emit(path)

    def _on_item_clicked(self, item, column):
        if not item:
            return
        data = item.data(0, Qt.UserRole)
        if isinstance(data, PromptFile):
            self.prompt_selected.emit(data)

    def _show_context_menu(self, position):
        item = self.tree.itemAt(position)
        if not item:
            return

        menu = QMenu(self)
        data = item.data(0, Qt.UserRole)
        is_folder = self._is_folder_item(item)
        is_all = item.text(0) == "全部"

        if is_all:
            menu.addAction("新建文件夹", lambda: self.new_folder_requested.emit(""))
            menu.addAction("新建文件", lambda: self.new_prompt_requested.emit(""))
        elif is_folder:
            menu.addAction("新建文件夹", lambda: self.new_folder_requested.emit(self._get_item_path(item)))
            menu.addAction("新建文件", lambda: self.new_prompt_requested.emit(self._get_item_path(item)))
            menu.addSeparator()
            menu.addAction("选择图标", lambda: self._choose_icon(item))
            menu.addAction("重命名", lambda: self.rename_folder_requested.emit(self._get_item_path(item)))
            menu.addAction("删除", lambda: self.delete_folder_requested.emit(self._get_item_path(item)))
        else:
            if isinstance(data, PromptFile):
                if isinstance(data, PromptFile):
                    rel = data.path.relative_to(config.data_dir).as_posix()
                    if state_service.is_favorite(rel):
                        menu.addAction("取消收藏", lambda: self._toggle_favorite(rel, False))
                    else:
                        menu.addAction("收藏", lambda: self._toggle_favorite(rel, True))
                    menu.addAction("复制内容", lambda: self._copy_prompt(data))
                    menu.addSeparator()
                    menu.addAction("重命名", lambda: self.rename_prompt_requested.emit(data))
                    menu.addAction("删除", lambda: self.delete_prompt_requested.emit(data))

        menu.exec(self.tree.mapToGlobal(position))

    def _choose_icon(self, item):
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QDialogButtonBox
        dialog = QDialog(self)
        dialog.setWindowTitle("选择文件夹图标")
        dialog.setMinimumWidth(300)
        layout = QVBoxLayout(dialog)

        btn_layout = QHBoxLayout()
        current_key = config.folder_icon(self._get_item_path(item))

        for key in _ICON_KEYS:
            if hasattr(self.style().StandardPixmap, key):
                icon = self.style().standardIcon(getattr(self.style().StandardPixmap, key))
                btn = QPushButton(icon, "")
                btn.setFixedSize(40, 40)
                btn.setCheckable(True)
                btn.setProperty("icon_key", key)
                if key == current_key:
                    btn.setChecked(True)

                def on_check(checked, k=key):
                    if checked:
                        for b in dialog.findChildren(QPushButton):
                            if b.property("icon_key") and b.property("icon_key") != k:
                                b.setChecked(False)
                        dialog.setProperty("selected_key", k)

                btn.clicked.connect(on_check)
                btn_layout.addWidget(btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        box.accepted.connect(dialog.accept)
        box.rejected.connect(dialog.reject)
        layout.addWidget(box)

        if dialog.exec() == QDialog.Accepted:
            selected = dialog.property("selected_key")
            if selected:
                folder_path = self._get_item_path(item)
                config.set_folder_icon(folder_path, selected)
                item.setIcon(0, self._folder_icon(folder_path))

    def _is_folder_item(self, item):
        if not item:
            return False
        return item.data(0, Qt.UserRole + 1) == "folder"

    def _get_item_path(self, item):
        if not item:
            return ""
        parts = []
        while item:
            text = item.text(0)
            if text != "全部":
                parts.insert(0, text)
            item = item.parent()
        return "/".join(parts)

    def load_tree(self):
        expanded_paths = self._get_expanded_paths()
        self.tree.clear()

        if not config.data_dir.exists():
            return

        all_item = QTreeWidgetItem(self.tree)
        all_item.setText(0, "全部")
        all_item.setIcon(0, self.style().standardIcon(self.style().StandardPixmap.SP_DirHomeIcon))
        all_item.setData(0, Qt.UserRole + 1, "folder")
        all_item.setExpanded(True)
        all_item.setFlags(all_item.flags() & ~Qt.ItemIsSelectable)

        favs = state_service.get_favorites()
        if favs:
            fav_item = QTreeWidgetItem(self.tree)
            fav_item.setText(0, "⭐ 收藏")
            fav_item.setIcon(0, self.style().standardIcon(self.style().StandardPixmap.SP_DialogApplyButton))
            fav_item.setData(0, Qt.UserRole + 1, "special")
            fav_item.setData(0, Qt.UserRole + 2, "favorites")
            fav_item.setExpanded(True)
            for fav_path in favs:
                full = config.data_dir / fav_path
                if full.exists():
                    child = QTreeWidgetItem(fav_item)
                    child.setText(0, full.stem)
                    child.setIcon(0, self.style().standardIcon(self.style().StandardPixmap.SP_FileIcon))
                    child.setData(0, Qt.UserRole, PromptFile(full))
                    child.setData(0, Qt.UserRole + 1, "file")

        recent = state_service.get_recent_files()
        if recent:
            recent_item = QTreeWidgetItem(self.tree)
            recent_item.setText(0, "🕐 最近使用")
            recent_item.setIcon(0, self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon))
            recent_item.setData(0, Qt.UserRole + 1, "special")
            recent_item.setData(0, Qt.UserRole + 2, "recent")
            recent_item.setExpanded(True)
            for r in recent[:20]:
                full = config.data_dir / r.get("path", "")
                if full.exists():
                    child = QTreeWidgetItem(recent_item)
                    child.setText(0, full.stem)
                    child.setIcon(0, self.style().standardIcon(self.style().StandardPixmap.SP_FileIcon))
                    child.setData(0, Qt.UserRole, PromptFile(full))
                    child.setData(0, Qt.UserRole + 1, "file")

        dirs = sorted([d for d in config.data_dir.iterdir() if d.is_dir() and not d.name.startswith(".")])
        files = sorted([f for f in config.data_dir.iterdir() if f.is_file() and f.suffix.lower() in config.supported_prompt_extensions])

        file_icon = self.style().standardIcon(self.style().StandardPixmap.SP_FileIcon)

        for d in dirs:
            rel_path = str(d.relative_to(config.data_dir)).replace("\\", "/")
            folder_item = QTreeWidgetItem(self.tree)
            folder_item.setText(0, d.name)
            folder_item.setIcon(0, self._folder_icon(rel_path))
            folder_item.setData(0, Qt.UserRole + 1, "folder")
            self._load_directory(d, folder_item)

        for f in files:
            file_item = QTreeWidgetItem(self.tree)
            file_item.setText(0, f.name)
            file_item.setIcon(0, file_icon)
            file_item.setData(0, Qt.UserRole, PromptFile(f))
            file_item.setData(0, Qt.UserRole + 1, "file")

        self._restore_expanded_paths(expanded_paths)

    def _get_expanded_paths(self):
        paths = set()
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            self._collect_expanded_paths(item, paths)
        return paths

    def _collect_expanded_paths(self, item, paths):
        if item.isExpanded():
            paths.add(self._get_item_path(item))
        for i in range(item.childCount()):
            self._collect_expanded_paths(item.child(i), paths)

    def _restore_expanded_paths(self, paths):
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            self._apply_expanded_paths(item, paths)

    def _apply_expanded_paths(self, item, paths):
        item_path = self._get_item_path(item)
        if item_path in paths:
            item.setExpanded(True)
        for i in range(item.childCount()):
            self._apply_expanded_paths(item.child(i), paths)

    def _load_directory(self, dir_path, parent_item):
        dirs = sorted([d for d in dir_path.iterdir() if d.is_dir() and not d.name.startswith(".")])
        files = sorted([f for f in dir_path.iterdir() if f.is_file() and f.suffix.lower() in config.supported_prompt_extensions])

        file_icon = self.style().standardIcon(self.style().StandardPixmap.SP_FileIcon)

        for d in dirs:
            rel_path = str(d.relative_to(config.data_dir)).replace("\\", "/")
            folder_item = QTreeWidgetItem(parent_item)
            folder_item.setText(0, d.name)
            folder_item.setIcon(0, self._folder_icon(rel_path))
            folder_item.setData(0, Qt.UserRole + 1, "folder")
            self._load_directory(d, folder_item)

        for f in files:
            file_item = QTreeWidgetItem(parent_item)
            file_item.setText(0, f.name)
            file_item.setIcon(0, file_icon)
            file_item.setData(0, Qt.UserRole, PromptFile(f))
            file_item.setData(0, Qt.UserRole + 1, "file")

    def _find_item_by_path(self, path):
        if not path:
            return None
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if self._get_item_path(item) == path:
                return item
            result = self._find_item_in_children(item, path)
            if result:
                return result
        return None

    def _find_item_in_children(self, parent, path):
        for i in range(parent.childCount()):
            child = parent.child(i)
            if self._get_item_path(child) == path:
                return child
            result = self._find_item_in_children(child, path)
            if result:
                return result
        return None

    def add_folder_item(self, parent_path, folder_name):
        folder_path = (Path(parent_path) / folder_name).as_posix() if parent_path else folder_name
        parent_item = self._find_item_by_path(parent_path) if parent_path else None
        if parent_item is None:
            parent_item = self.tree
        folder_item = QTreeWidgetItem(parent_item)
        folder_item.setText(0, folder_name)
        folder_item.setIcon(0, self._folder_icon(folder_path))
        folder_item.setData(0, Qt.UserRole + 1, "folder")
        self.tree.setCurrentItem(folder_item)
        parent_item.setExpanded(True)

    def add_prompt_item(self, parent_path, prompt):
        parent_item = self._find_item_by_path(parent_path) if parent_path else None
        if parent_item is None:
            parent_item = self.tree
        file_icon = self.style().standardIcon(self.style().StandardPixmap.SP_FileIcon)
        file_item = QTreeWidgetItem(parent_item)
        file_item.setText(0, prompt.path.name)
        file_item.setIcon(0, file_icon)
        file_item.setData(0, Qt.UserRole, prompt)
        file_item.setData(0, Qt.UserRole + 1, "file")
        self.tree.setCurrentItem(file_item)
        parent_item.setExpanded(True)

    def remove_folder_item(self, folder_path):
        item = self._find_item_by_path(folder_path)
        if item:
            parent = item.parent()
            if parent:
                parent.removeChild(item)
            else:
                index = self.tree.indexOfTopLevelItem(item)
                self.tree.takeTopLevelItem(index)

    def remove_prompt_item(self, prompt):
        item = self._find_item_by_path(str(prompt.rel_path).replace("\\", "/"))
        if item:
            parent = item.parent()
            if parent:
                parent.removeChild(item)
            else:
                index = self.tree.indexOfTopLevelItem(item)
                self.tree.takeTopLevelItem(index)

    def rename_folder_item(self, folder_path, new_name):
        item = self._find_item_by_path(folder_path)
        if item:
            item.setText(0, new_name)
            new_path = str(Path(folder_path).parent / new_name).replace("\\", "/")
            if new_path.startswith("./"):
                new_path = new_path[2:]
            item.setIcon(0, self._folder_icon(new_path))

    def _copy_prompt(self, prompt: PromptFile):
        from app.services.clipboard_service import clipboard_service
        from app.services.state_service import state_service
        content = prompt.read_content()
        if clipboard_service.copy_text(content):
            rel = prompt.path.relative_to(config.data_dir).as_posix()
            state_service.add_recent_file(rel)

    def _toggle_favorite(self, file_path: str, add: bool):
        if add:
            state_service.add_favorite(file_path)
        else:
            state_service.remove_favorite(file_path)
        self.load_tree()

    def rename_prompt_item(self, prompt, new_name):
        item = self._find_item_by_path(str(prompt.rel_path).replace("\\", "/"))
        if item:
            item.setText(0, f"{new_name}{prompt.extension}")

    def _on_batch_move(self):
        items = self.tree.selectedItems()
        prompts = [item.data(0, Qt.UserRole) for item in items if isinstance(item.data(0, Qt.UserRole), PromptFile)]
        if not prompts:
            QMessageBox.information(self, "批量移动", "请先选择要移动的文件")
            return
        from PySide6.QtWidgets import QInputDialog
        categories = file_service.get_categories()
        if not categories:
            QMessageBox.information(self, "批量移动", "没有可用的分类")
            return
        category, ok = QInputDialog.getItem(self, "批量移动", "移动到分类:", categories, 0, False)
        if ok and category:
            for prompt in prompts:
                new_path = file_service._resolve_path(category) / prompt.path.name
                if new_path.exists() and new_path != prompt.path:
                    continue
                try:
                    prompt.path.rename(new_path)
                except Exception:
                    pass
            search_service.rebuild_index()
            self.load_tree()

    def _on_batch_delete(self):
        items = self.tree.selectedItems()
        prompts = [item.data(0, Qt.UserRole) for item in items if isinstance(item.data(0, Qt.UserRole), PromptFile)]
        if not prompts:
            QMessageBox.information(self, "批量删除", "请先选择要删除的文件")
            return
        reply = QMessageBox.question(
            self,
            "确认批量删除",
            f'确定要删除 {len(prompts)} 个提示词吗？\n该操作不可恢复。',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            for prompt in prompts:
                rel = prompt.path.relative_to(config.data_dir).as_posix()
                if file_service.delete_prompt(prompt):
                    search_service.remove_index_file(rel)
            self.load_tree()

    def _on_open_containing_folder(self):
        items = self.tree.selectedItems()
        prompts = [item.data(0, Qt.UserRole) for item in items if isinstance(item.data(0, Qt.UserRole), PromptFile)]
        if not prompts:
            QMessageBox.information(self, "打开文件夹", "请先选择要打开的文件")
            return
        import subprocess
        import sys
        prompt = prompts[0]
        folder = str(prompt.path.parent)
        try:
            if sys.platform == "win32":
                subprocess.run(["explorer", "/select,", str(prompt.path)])
            elif sys.platform == "darwin":
                subprocess.run(["open", "-R", str(prompt.path)])
            else:
                subprocess.run(["xdg-open", folder])
        except Exception:
            pass

    def _on_batch_export(self):
        items = self.tree.selectedItems()
        prompts = [item.data(0, Qt.UserRole) for item in items if isinstance(item.data(0, Qt.UserRole), PromptFile)]
        if not prompts:
            QMessageBox.information(self, "批量导出", "请先选择要导出的文件")
            return
        dest_dir = QFileDialog.getExistingDirectory(self, "选择导出目录")
        if not dest_dir:
            return
        dest = Path(dest_dir)
        exported = 0
        for prompt in prompts:
            target = dest / prompt.path.name
            counter = 1
            while target.exists():
                target = dest / f"{prompt.path.stem}_{counter}{prompt.path.suffix}"
                counter += 1
            try:
                shutil.copy2(str(prompt.path), str(target))
                exported += 1
            except Exception:
                pass
        if exported > 0:
            QMessageBox.information(self, "批量导出", f"成功导出 {exported} 个文件")

    def select_category(self, category: str):
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item.text(0) == category and self._is_folder_item(item):
                self.tree.setCurrentItem(item)
                item.setExpanded(True)
                return True
        return False

    def select_prompt(self, prompt):
        self._select_prompt_in_item(self.tree.invisibleRootItem(), prompt)

    def _select_prompt_in_item(self, parent, prompt):
        for i in range(parent.childCount()):
            child = parent.child(i)
            data = child.data(0, Qt.UserRole)
            if isinstance(data, PromptFile) and data.path == prompt.path:
                self.tree.setCurrentItem(child)
                parent = child.parent()
                while parent:
                    parent.setExpanded(True)
                    parent = parent.parent()
                return True
            if self._is_folder_item(child):
                if self._select_prompt_in_item(child, prompt):
                    return True
        return False


