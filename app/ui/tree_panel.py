from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.config import config
from app.constants import AppConstants
from app.services.file_service import PromptFile, file_service


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

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setFrameShape(QTreeWidget.NoFrame)
        self.tree.itemClicked.connect(self._on_item_clicked)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.tree)

    def _on_new_folder(self):
        current = self.tree.currentItem()
        path = self._get_item_path(current) if current else ""
        if path and not self._is_folder_item(current):
            path = str(Path(path).parent)
        self.new_folder_requested.emit(path)

    def _on_new_prompt(self):
        current = self.tree.currentItem()
        path = self._get_item_path(current) if current else ""
        if path and not self._is_folder_item(current):
            path = str(Path(path).parent)
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

        if is_folder:
            menu.addAction("新建文件夹", lambda: self.new_folder_requested.emit(self._get_item_path(item)))
            menu.addAction("新建文件", lambda: self.new_prompt_requested.emit(self._get_item_path(item)))
            menu.addSeparator()
            menu.addAction("重命名", lambda: self.rename_folder_requested.emit(self._get_item_path(item)))
            menu.addAction("删除", lambda: self.delete_folder_requested.emit(self._get_item_path(item)))
        else:
            if isinstance(data, PromptFile):
                menu.addAction("重命名", lambda: self.rename_prompt_requested.emit(data))
                menu.addAction("删除", lambda: self.delete_prompt_requested.emit(data))

        menu.exec(self.tree.mapToGlobal(position))

    def _is_folder_item(self, item) -> bool:
        if not item:
            return False
        return item.data(0, Qt.UserRole + 1) == "folder"

    def _get_item_path(self, item) -> str:
        if not item:
            return ""
        parts = []
        while item:
            parts.insert(0, item.text(0))
            item = item.parent()
        return "/".join(parts[1:]) if len(parts) > 1 else ""

    def load_tree(self):
        self.tree.clear()
        root = QTreeWidgetItem(self.tree)
        root.setText(0, "全部")
        root.setData(0, Qt.UserRole + 1, "folder")
        root.setExpanded(True)

        if not config.data_dir.exists():
            return

        self._load_directory(config.data_dir, root)

    def _load_directory(self, dir_path: Path, parent_item: QTreeWidgetItem):
        dirs = sorted([d for d in dir_path.iterdir() if d.is_dir() and not d.name.startswith(".")])
        files = sorted([f for f in dir_path.iterdir() if f.is_file() and f.suffix.lower() in AppConstants.SUPPORTED_EXTENSIONS])

        for d in dirs:
            folder_item = QTreeWidgetItem(parent_item)
            folder_item.setText(0, d.name)
            folder_item.setData(0, Qt.UserRole + 1, "folder")
            self._load_directory(d, folder_item)

        for f in files:
            file_item = QTreeWidgetItem(parent_item)
            file_item.setText(0, f.name)
            file_item.setData(0, Qt.UserRole, PromptFile(f))
            file_item.setData(0, Qt.UserRole + 1, "file")

    def select_prompt(self, prompt: PromptFile):
        self._select_prompt_in_item(self.tree.invisibleRootItem(), prompt)

    def _select_prompt_in_item(self, parent: QTreeWidgetItem, prompt: PromptFile) -> bool:
        for i in range(parent.childCount()):
            child = parent.child(i)
            data = child.data(0, Qt.UserRole)
            if isinstance(data, PromptFile) and data.path == prompt.path:
                self.tree.setCurrentItem(child)
                return True
            if self._is_folder_item(child):
                if self._select_prompt_in_item(child, prompt):
                    return True
        return False

    def get_selected_path(self) -> str:
        item = self.tree.currentItem()
        return self._get_item_path(item)

    def get_selected_prompt(self) -> PromptFile:
        item = self.tree.currentItem()
        if item:
            data = item.data(0, Qt.UserRole)
            if isinstance(data, PromptFile):
                return data
        return None
