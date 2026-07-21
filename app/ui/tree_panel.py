import shutil
from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.config import config
from app.services.file_service import PromptFile, file_service
from app.services.search_service import search_service
from app.services.state_service import state_service
from app.ui.theme import current_palette, tree_stylesheet
from app.utils.icon_utils import create_theme_icon

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


class SidebarItemDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._palette = current_palette()

    def refresh_theme(self):
        self._palette = current_palette()

    def paint(self, painter: QPainter, option, index):
        view_option = QStyleOptionViewItem(option)
        self.initStyleOption(view_option, index)
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        row = option.rect.adjusted(5, 2, -5, -2)
        selected = bool(option.state & QStyle.State_Selected)
        hovered = bool(option.state & QStyle.State_MouseOver)
        if selected:
            painter.setPen(QPen(QColor(self._palette["hairline_strong"]), 1))
            painter.setBrush(QColor(self._palette["surface_active"]))
            painter.drawRoundedRect(row, 10, 10)
            marker = row.adjusted(3, 8, 0, -8)
            marker.setWidth(3)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(self._palette["accent"]))
            painter.drawRoundedRect(marker, 2, 2)
        elif hovered:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(self._palette["surface_hover"]))
            painter.drawRoundedRect(row, 10, 10)

        icon_rect = row.adjusted(11, 0, 0, 0)
        icon_rect.setWidth(18)
        icon_rect.setHeight(18)
        icon_rect.moveCenter(row.center())
        icon_rect.moveLeft(row.left() + 12)
        icon = index.data(Qt.DecorationRole)
        if icon:
            icon.paint(painter, icon_rect, Qt.AlignCenter)

        item_role = index.data(Qt.UserRole + 1)
        is_top_level = not index.parent().isValid()
        font = QFont(view_option.font)
        if is_top_level or item_role in ("folder", "special"):
            font.setWeight(QFont.DemiBold)
        painter.setFont(font)
        painter.setPen(
            QColor(self._palette["ink"] if selected or is_top_level else self._palette["body"])
        )
        text_rect = row.adjusted(40, 0, -10, 0)
        text = view_option.fontMetrics.elidedText(
            view_option.text,
            Qt.ElideRight,
            max(20, text_rect.width()),
        )
        painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, text)
        painter.restore()

    def sizeHint(self, option, index):
        height = 42 if not index.parent().isValid() else 38
        return QSize(super().sizeHint(option, index).width(), height)


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
        from app.constants import Messages
        if not item:
            return ""
        parts = []
        while item:
            text = self.parent()._item_name(item) if self.parent() else item.text(0)
            if text not in (Messages.ALL_PROMPTS, Messages.FAVORITES, Messages.RECENTLY_USED):
                parts.insert(0, text)
            item = item.parent()
        return "/".join(parts)

    def _is_folder_item(self, item):
        if not item:
            return False
        return item.data(0, Qt.UserRole + 1) == "folder"

    def dragMoveEvent(self, event):
        target = self.itemAt(event.position().toPoint())
        dragged_items = self.selectedItems()
        if not target or not dragged_items:
            event.ignore()
            return
        dragged = dragged_items[0]
        dragged_data = dragged.data(0, Qt.UserRole)
        target_data = target.data(0, Qt.UserRole)
        same_folder_file_reorder = (
            isinstance(dragged_data, PromptFile)
            and isinstance(target_data, PromptFile)
            and dragged.parent() == target.parent()
        )
        if same_folder_file_reorder or self._is_folder_item(target):
            event.accept()
            return
        event.ignore()

    def dropEvent(self, event):
        target = self.itemAt(event.position().toPoint())
        if not target:
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

        dragged_data = dragged.data(0, Qt.UserRole)
        target_data = target.data(0, Qt.UserRole)
        if isinstance(dragged_data, PromptFile) and isinstance(target_data, PromptFile):
            source_parent = dragged.parent()
            target_parent = target.parent()
            if source_parent == target_parent:
                source_path = self._get_item_path(dragged)
                folder_path = self._get_item_path(source_parent) if source_parent else ""
                drop_below = event.position().toPoint().y() > self.visualItemRect(target).center().y()
                if source_parent:
                    source_index = source_parent.indexOfChild(dragged)
                    target_index = source_parent.indexOfChild(target)
                    moved_item = source_parent.takeChild(source_index)
                    if source_index < target_index:
                        target_index -= 1
                    insert_index = target_index + 1 if drop_below else target_index
                    source_parent.insertChild(insert_index, moved_item)
                else:
                    source_index = self.indexOfTopLevelItem(dragged)
                    target_index = self.indexOfTopLevelItem(target)
                    moved_item = self.takeTopLevelItem(source_index)
                    if source_index < target_index:
                        target_index -= 1
                    insert_index = target_index + 1 if drop_below else target_index
                    self.insertTopLevelItem(insert_index, moved_item)
                self.setCurrentItem(moved_item)
                self.parent().save_folder_order_for_item(source_parent)
                self.item_moved.emit(source_path, folder_path)
                event.accept()
                return

        if not self._is_folder_item(target):
            event.ignore()
            return

        source_path = self._get_item_path(dragged)
        target_path = self._get_item_path(target)
        from app.constants import Messages
        is_target_root = target.text(0) == Messages.ALL_PROMPTS

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
                if source_parent == ".":
                    source_parent = ""
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
        self.parent().save_folder_order(source_parent if "source_parent" in locals() else "")
        self.parent().save_folder_order(target_path)
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
    folder_selected = Signal(str)
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
        from app.constants import Messages

        self.setObjectName("sidebarCard")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(10, 10, 10, 10)
        self._layout.setSpacing(10)

        self.header_host = QWidget()
        self.header_host.setObjectName("sidebarHeader")
        header = QHBoxLayout(self.header_host)
        header.setContentsMargins(4, 2, 2, 2)
        header.setSpacing(8)
        self.header_text_host = QWidget()
        header_text = QVBoxLayout(self.header_text_host)
        header_text.setContentsMargins(0, 0, 0, 0)
        header_text.setSpacing(2)
        self.header_label = QLabel(Messages.SIDEBAR_TITLE)
        self.header_label.setObjectName("sidebarTitle")
        self.summary_label = QLabel("你的 Prompt 工作空间")
        self.summary_label.setObjectName("sidebarCaption")
        header_text.addWidget(self.header_label)
        header_text.addWidget(self.summary_label)
        header.addWidget(self.header_text_host, 1)
        header.addStretch()

        self.collapse_btn = QPushButton("‹")
        self.collapse_btn.setProperty("role", "icon")
        self.collapse_btn.setFixedSize(24, 24)
        self.collapse_btn.setToolTip("收起侧边栏")
        self.collapse_btn.clicked.connect(self._toggle_collapse)
        header.addWidget(self.collapse_btn)
        self._layout.addWidget(self.header_host)

        self.quick_actions_host = QWidget()
        self.quick_actions_host.setObjectName("sidebarActions")
        quick_actions = QHBoxLayout(self.quick_actions_host)
        quick_actions.setContentsMargins(0, 0, 0, 0)
        quick_actions.setSpacing(6)
        self.new_prompt_btn = QPushButton("＋ Prompt")
        self.new_prompt_btn.setProperty("role", "sidebarPrimary")
        self.new_prompt_btn.clicked.connect(self._on_new_prompt)
        quick_actions.addWidget(self.new_prompt_btn, 1)
        self.new_folder_btn = QPushButton("新建文件夹")
        self.new_folder_btn.setProperty("role", "sidebarSoft")
        self.new_folder_btn.clicked.connect(self._on_new_folder)
        quick_actions.addWidget(self.new_folder_btn, 1)
        self._layout.addWidget(self.quick_actions_host)

        self.tree = DraggableTreeWidget(self)
        self.tree.setObjectName("promptTree")
        self.tree.setHeaderHidden(True)
        self.tree.setRootIsDecorated(False)
        self.tree.setItemsExpandable(True)
        self.tree.setIndentation(16)
        self.tree.setFrameShape(QTreeWidget.NoFrame)
        self.tree.itemClicked.connect(self._on_item_clicked)
        self.tree.itemExpanded.connect(self._on_item_expanded)
        self.tree.itemCollapsed.connect(self._on_item_collapsed)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        self.tree_delegate = SidebarItemDelegate(self.tree)
        self.tree.setItemDelegate(self.tree_delegate)
        self.tree.setStyleSheet(tree_stylesheet())
        self._layout.addWidget(self.tree, 1)

        self.footer_label = QLabel("拖拽排序  ·  右键管理")
        self.footer_label.setObjectName("sidebarFooter")
        self.footer_label.setAlignment(Qt.AlignCenter)
        self._layout.addWidget(self.footer_label)

        self._collapsed = False
        self._original_width = config.ui_sidebar_width

    def apply_theme(self):
        self.tree_delegate.refresh_theme()
        self._refresh_tree_icons()
        self.tree.setStyleSheet(tree_stylesheet())
        self.tree.viewport().update()

    def _toggle_collapse(self):
        parent = self.parentWidget()
        if not parent:
            return
        splitter = parent if isinstance(parent, QSplitter) else None
        if splitter is None:
            for child in parent.children():
                if isinstance(child, QSplitter):
                    splitter = child
                    break
        if not splitter:
            return
        if self._collapsed:
            self.setMaximumWidth(340)
            self.setMinimumWidth(220)
            self._layout.setContentsMargins(10, 10, 10, 10)
            self.header_host.layout().setContentsMargins(4, 2, 2, 2)
            self.collapse_btn.setText("‹")
            self.collapse_btn.setToolTip("收起侧边栏")
            if splitter.count() >= 2:
                splitter.setSizes([self._original_width, splitter.width() - self._original_width])
            for widget in (
                self.header_text_host,
                self.quick_actions_host,
                self.tree,
                self.footer_label,
            ):
                widget.setVisible(True)
            self._collapsed = False
        else:
            self._original_width = self.width()
            self.setMaximumWidth(40)
            self.setMinimumWidth(40)
            self._layout.setContentsMargins(6, 8, 6, 8)
            self.header_host.layout().setContentsMargins(0, 0, 0, 0)
            self.collapse_btn.setText("›")
            self.collapse_btn.setToolTip("展开侧边栏")
            for widget in (
                self.header_text_host,
                self.quick_actions_host,
                self.tree,
                self.footer_label,
            ):
                widget.setVisible(False)
            self._collapsed = True

    def _folder_icon(self, folder_path):
        icon_key = config.folder_icon(folder_path)
        if icon_key and hasattr(self.style().StandardPixmap, icon_key):
            return self.style().standardIcon(getattr(self.style().StandardPixmap, icon_key))
        return create_theme_icon("folder", current_palette()["accent"])

    def _file_icon(self):
        return create_theme_icon("file", current_palette()["muted"])

    def _special_icon(self, kind: str):
        icon_kind = {
            "favorites": "star",
            "recent": "clock",
            "all": "library",
        }.get(kind, "library")
        return create_theme_icon(icon_kind, current_palette()["accent"])

    def _refresh_tree_icons(self):
        def refresh(item):
            item_type = item.data(0, Qt.UserRole + 1)
            special = item.data(0, Qt.UserRole + 2)
            if special in ("all", "favorites", "recent"):
                item.setIcon(0, self._special_icon(special))
            elif item_type == "folder":
                item.setIcon(0, self._folder_icon(self._get_item_path(item)))
            elif item_type == "file":
                item.setIcon(0, self._file_icon())
            for index in range(item.childCount()):
                refresh(item.child(index))

        for index in range(self.tree.topLevelItemCount()):
            refresh(self.tree.topLevelItem(index))

    def _set_item_name(self, item, name: str):
        item.setData(0, Qt.UserRole + 3, name)
        self._refresh_item_arrow(item)

    def _item_name(self, item) -> str:
        stored = item.data(0, Qt.UserRole + 3)
        return stored if stored else item.text(0).lstrip("▾▸ ").strip()

    def _refresh_item_arrow(self, item):
        name = self._item_name(item)
        if self._is_folder_item(item) and item.childCount() > 0:
            prefix = "▾" if item.isExpanded() else "▸"
            item.setText(0, f"{prefix} {name}")
        else:
            item.setText(0, name)

    def _on_item_expanded(self, item):
        self._refresh_item_arrow(item)

    def _on_item_collapsed(self, item):
        self._refresh_item_arrow(item)

    def _ordered_files(self, folder_path: str, files: list[Path]) -> list[Path]:
        ordered_names = state_service.get_folder_order(folder_path)
        if not ordered_names:
            return sorted(files)
        by_name = {file.name: file for file in files}
        ordered = [by_name[name] for name in ordered_names if name in by_name]
        remaining = sorted([file for file in files if file.name not in ordered_names])
        return ordered + remaining

    def save_folder_order_for_item(self, parent_item):
        folder_path = self._get_item_path(parent_item) if parent_item else ""
        self.save_folder_order(folder_path, parent_item)

    def save_folder_order(self, folder_path: str, parent_item=None):
        if parent_item is None:
            parent_item = self._find_item_by_path(folder_path) if folder_path else None
        if parent_item is None:
            count = self.tree.topLevelItemCount()
            items = [self.tree.topLevelItem(i) for i in range(count)]
        else:
            items = [parent_item.child(i) for i in range(parent_item.childCount())]
        file_names = []
        for item in items:
            data = item.data(0, Qt.UserRole)
            if isinstance(data, PromptFile):
                file_names.append(data.path.name)
        state_service.set_folder_order(folder_path, file_names)

    def get_prompts_for_folder(self, folder_path: str) -> list[PromptFile]:
        if not folder_path:
            return list(file_service.iter_all_prompts())
        target_dir = config.data_dir / folder_path if folder_path else config.data_dir
        if not target_dir.exists():
            return []
        files = [
            file for file in target_dir.iterdir()
            if file.is_file() and file.suffix.lower() in config.supported_prompt_extensions
        ]
        return [PromptFile(file) for file in self._ordered_files(folder_path, files)]

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
        elif self._is_folder_item(item):
            self.folder_selected.emit(self._get_item_path(item))

    def _show_context_menu(self, position):
        from app.constants import Messages
        item = self.tree.itemAt(position)
        if not item:
            return

        menu = QMenu(self)
        data = item.data(0, Qt.UserRole)
        is_folder = self._is_folder_item(item)
        is_all = item.text(0) == Messages.ALL_PROMPTS

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
                rel = data.path.relative_to(config.data_dir).as_posix()
                if state_service.is_favorite(rel):
                    menu.addAction("取消收藏", lambda: self._toggle_favorite(rel, False))
                else:
                    menu.addAction("收藏", lambda: self._toggle_favorite(rel, True))
                menu.addAction("复制内容", lambda: self._copy_prompt(data))
                menu.addAction("加入组合器", lambda: self._add_to_composer(data))
                menu.addAction("打开所在文件夹", lambda: self._open_containing_folder(data))
                menu.addAction("查看历史版本", lambda: self._show_version_history(data))
                menu.addSeparator()
                menu.addAction("重命名", lambda: self.rename_prompt_requested.emit(data))
                selected = self.tree.selectedItems()
                prompts = [it.data(0, Qt.UserRole) for it in selected if isinstance(it.data(0, Qt.UserRole), PromptFile)]
                if len(prompts) > 1:
                    menu.addAction(f"删除({len(prompts)}个文件)", lambda: self._on_batch_delete())
                else:
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
        from app.constants import Messages
        if not item:
            return ""
        parts = []
        while item:
            text = self._item_name(item)
            if text not in (Messages.ALL_PROMPTS, Messages.FAVORITES, Messages.RECENTLY_USED):
                parts.insert(0, text)
            item = item.parent()
        return "/".join(parts)

    def load_tree(self):
        from app.constants import Messages
        expanded_paths = self._get_expanded_paths()
        self.tree.clear()

        if not config.data_dir.exists():
            self.summary_label.setText("数据目录尚未创建")
            return

        all_item = QTreeWidgetItem(self.tree)
        all_item.setIcon(0, self._special_icon("all"))
        all_item.setData(0, Qt.UserRole + 1, "folder")
        all_item.setData(0, Qt.UserRole + 2, "all")
        all_item.setExpanded(True)
        self._set_item_name(all_item, Messages.ALL_PROMPTS)

        favs = state_service.get_favorites()
        if favs:
            fav_item = QTreeWidgetItem(self.tree)
            fav_item.setIcon(0, self._special_icon("favorites"))
            fav_item.setData(0, Qt.UserRole + 1, "special")
            fav_item.setData(0, Qt.UserRole + 2, "favorites")
            fav_item.setExpanded(True)
            self._set_item_name(fav_item, Messages.FAVORITES)
            for fav_path in favs:
                full = config.data_dir / fav_path
                if full.exists():
                    child = QTreeWidgetItem(fav_item)
                    child.setText(0, full.name)
                    child.setIcon(0, self._file_icon())
                    child.setData(0, Qt.UserRole, PromptFile(full))
                    child.setData(0, Qt.UserRole + 1, "file")

        recent = state_service.get_recent_files()
        if recent:
            recent_item = QTreeWidgetItem(self.tree)
            recent_item.setIcon(0, self._special_icon("recent"))
            recent_item.setData(0, Qt.UserRole + 1, "special")
            recent_item.setData(0, Qt.UserRole + 2, "recent")
            recent_item.setExpanded(False)
            self._set_item_name(recent_item, Messages.RECENTLY_USED)
            for r in recent[:20]:
                full = config.data_dir / r.get("path", "")
                if full.exists():
                    child = QTreeWidgetItem(recent_item)
                    child.setText(0, full.name)
                    child.setIcon(0, self._file_icon())
                    child.setData(0, Qt.UserRole, PromptFile(full))
                    child.setData(0, Qt.UserRole + 1, "file")

        dirs = sorted([d for d in config.data_dir.iterdir() if d.is_dir() and not d.name.startswith(".")])
        files = self._ordered_files("", [f for f in config.data_dir.iterdir() if f.is_file() and f.suffix.lower() in config.supported_prompt_extensions])

        file_icon = self._file_icon()

        for d in dirs:
            rel_path = str(d.relative_to(config.data_dir)).replace("\\", "/")
            folder_item = QTreeWidgetItem(self.tree)
            folder_item.setIcon(0, self._folder_icon(rel_path))
            folder_item.setData(0, Qt.UserRole + 1, "folder")
            self._set_item_name(folder_item, d.name)
            self._load_directory(d, folder_item)
            self._refresh_item_arrow(folder_item)

        for f in files:
            file_item = QTreeWidgetItem(self.tree)
            file_item.setText(0, f.name)
            file_item.setIcon(0, file_icon)
            file_item.setData(0, Qt.UserRole, PromptFile(f))
            file_item.setData(0, Qt.UserRole + 1, "file")

        prompt_count = sum(1 for _ in file_service.iter_all_prompts())
        self.summary_label.setText(f"{prompt_count} 个 Prompt · 主题已同步")
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
        folder_path = dir_path.relative_to(config.data_dir).as_posix()
        files = self._ordered_files(folder_path, [f for f in dir_path.iterdir() if f.is_file() and f.suffix.lower() in config.supported_prompt_extensions])

        file_icon = self._file_icon()

        for d in dirs:
            rel_path = str(d.relative_to(config.data_dir)).replace("\\", "/")
            folder_item = QTreeWidgetItem(parent_item)
            folder_item.setIcon(0, self._folder_icon(rel_path))
            folder_item.setData(0, Qt.UserRole + 1, "folder")
            self._set_item_name(folder_item, d.name)
            self._load_directory(d, folder_item)
            self._refresh_item_arrow(folder_item)

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
        folder_item.setIcon(0, self._folder_icon(folder_path))
        folder_item.setData(0, Qt.UserRole + 1, "folder")
        self._set_item_name(folder_item, folder_name)
        self.tree.setCurrentItem(folder_item)
        parent_item.setExpanded(True) if isinstance(parent_item, QTreeWidgetItem) else None

    def add_prompt_item(self, parent_path, prompt):
        parent_item = self._find_item_by_path(parent_path) if parent_path else None
        if parent_item is None:
            parent_item = self.tree
        file_icon = self._file_icon()
        file_item = QTreeWidgetItem(parent_item)
        file_item.setText(0, prompt.path.name)
        file_item.setIcon(0, file_icon)
        file_item.setData(0, Qt.UserRole, prompt)
        file_item.setData(0, Qt.UserRole + 1, "file")
        self.tree.setCurrentItem(file_item)
        parent_item.setExpanded(True) if isinstance(parent_item, QTreeWidgetItem) else None

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
            self._set_item_name(item, new_name)
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
            from app.services.usage_service import usage_service
            usage_service.record_copy(rel)

    def _add_to_composer(self, prompt: PromptFile):
        from app.services.composer_service import composer_service
        rel = prompt.path.relative_to(config.data_dir).as_posix()
        if composer_service.add_file(rel):
            QMessageBox.information(self, "加入成功", f"已将 {prompt.name} 加入组合器")
        else:
            QMessageBox.information(self, "提示", f"{prompt.name} 已在组合器中")

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
            main_win = self.window()
            main_win._skip_watcher = True
            for prompt in prompts:
                new_path = file_service._resolve_path(category) / prompt.path.name
                if new_path.exists() and new_path != prompt.path:
                    continue
                try:
                    prompt.path.rename(new_path)
                except Exception:
                    pass
            main_win._skip_watcher = False
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
            main_win = self.window()
            main_win._skip_watcher = True
            for prompt in prompts:
                rel = prompt.path.relative_to(config.data_dir).as_posix()
                if file_service.delete_prompt(prompt):
                    search_service.remove_index_file(rel)
            main_win._skip_watcher = False
            search_service.rebuild_index()
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

    def _show_version_history(self, prompt_file):
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QTextEdit, QDialogButtonBox
        from app.services.history_service import history_service
        versions = history_service.list_versions(prompt_file.path)
        if not versions:
            QMessageBox.information(self, "历史版本", "暂无历史版本")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle(f"历史版本 - {prompt_file.path.name}")
        dialog.setMinimumSize(600, 400)
        layout = QVBoxLayout(dialog)
        version_list = QListWidget()
        for v in versions:
            version_list.addItem(f"{v['timestamp']} ({v['size']} 字节)")
        layout.addWidget(QLabel(f"共 {len(versions)} 个历史版本"))
        layout.addWidget(version_list)
        preview = QTextEdit()
        preview.setReadOnly(True)
        layout.addWidget(preview)

        def on_select():
            idx = version_list.currentRow()
            if 0 <= idx < len(versions):
                content = history_service.get_version_content(versions[idx]["path"])
                preview.setPlainText(content if content else "(无法读取)")

        version_list.currentRowChanged.connect(lambda _: on_select())

        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        restore_btn = buttons.addButton("恢复此版本", QDialogButtonBox.ActionRole)
        def do_restore():
            idx = version_list.currentRow()
            if 0 <= idx < len(versions):
                ok = history_service.restore_version(prompt_file.path, versions[idx]["path"])
                QMessageBox.information(dialog, "恢复版本", "版本已恢复" if ok else "恢复失败")
        restore_btn.clicked.connect(do_restore)
        buttons.accepted.connect(dialog.accept)
        layout.addWidget(buttons)
        dialog.exec()

    def _open_containing_folder(self, prompt_file):
        import os
        folder = prompt_file.path.parent
        try:
            os.startfile(str(folder))
        except Exception:
            pass
