from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
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
from app.constants import AppConstants
from app.services.file_service import PromptFile, file_service

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
                import shutil
                shutil.move(str(Path(config.data_dir) / source_path), str(dest))
                new_rel = str(dest.relative_to(config.data_dir)).replace("\\", "/")
                icon_key = config.folder_icon(source_path)
                if icon_key:
                    config.set_folder_icon(new_rel, icon_key)
                    config.set_folder_icon(source_path, "")
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
                    import shutil
                    shutil.move(str(data.path), str(dest))
                except Exception as e:
                    QMessageBox.warning(self, "错误", f"移动失败: {e}")
                    event.ignore()
                    return

        self.item_moved.emit(source_path, target_path)
        event.accept()


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
        self.tree.item_moved.connect(self._on_item_moved)
        layout.addWidget(self.tree)

    def _on_item_moved(self, source_path, target_path):
        self.load_tree()

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
        self.tree.clear()

        if not config.data_dir.exists():
            return

        all_item = QTreeWidgetItem(self.tree)
        all_item.setText(0, "全部")
        all_item.setIcon(0, self.style().standardIcon(self.style().StandardPixmap.SP_DirHomeIcon))
        all_item.setData(0, Qt.UserRole + 1, "folder")
        all_item.setExpanded(True)
        all_item.setFlags(all_item.flags() & ~Qt.ItemIsSelectable)

        dirs = sorted([d for d in config.data_dir.iterdir() if d.is_dir() and not d.name.startswith(".")])
        files = sorted([f for f in config.data_dir.iterdir() if f.is_file() and f.suffix.lower() in AppConstants.SUPPORTED_EXTENSIONS])

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

    def _load_directory(self, dir_path, parent_item):
        dirs = sorted([d for d in dir_path.iterdir() if d.is_dir() and not d.name.startswith(".")])
        files = sorted([f for f in dir_path.iterdir() if f.is_file() and f.suffix.lower() in AppConstants.SUPPORTED_EXTENSIONS])

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

    def get_selected_path(self):
        item = self.tree.currentItem()
        return self._get_item_path(item)

    def get_selected_prompt(self):
        item = self.tree.currentItem()
        if item:
            data = item.data(0, Qt.UserRole)
            if isinstance(data, PromptFile):
                return data
        return None
