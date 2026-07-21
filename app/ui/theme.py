import re
from copy import deepcopy
from pathlib import Path

from app.ui.theme_pack import (
    load_theme_pack,
    theme_pack_asset,
    theme_pack_variant,
    theme_pack_variants,
)


LIGHT_PALETTE = {
    "canvas": "#F8F7F3",
    "surface": "#F2EFE8",
    "surface_elevated": "#FFFFFF",
    "surface_panel": "#FBFAF7",
    "surface_hover": "#EDE9E1",
    "surface_active": "#EAF2EE",
    "hairline": "#E6E0D6",
    "hairline_soft": "rgba(36, 34, 30, 0.08)",
    "hairline_strong": "#D6CEC1",
    "ink": "#25231F",
    "body": "#555149",
    "muted": "#777168",
    "subtle": "#948D82",
    "primary": "#2B2A26",
    "on_primary": "#FFFFFF",
    "accent": "#6D8B78",
    "accent_hover": "#526F5E",
    "accent_soft": "rgba(109, 139, 120, 0.16)",
    "success": "#4F8F68",
    "warning": "#C59A38",
    "error": "#D96262",
    "highlight": "#F2D680",
}

DARK_PALETTE = {
    "canvas": "#252521",
    "surface": "#2C2B27",
    "surface_elevated": "#34332F",
    "surface_panel": "#302F2B",
    "surface_hover": "#3B3934",
    "surface_active": "#3A443E",
    "hairline": "#47443D",
    "hairline_soft": "rgba(255, 255, 255, 0.09)",
    "hairline_strong": "#5A554D",
    "ink": "#F2F0E8",
    "body": "#D8D2C6",
    "muted": "#AFA79A",
    "subtle": "#817A70",
    "primary": "#F4F0E7",
    "on_primary": "#26231F",
    "accent": "#86A891",
    "accent_hover": "#A3C4AD",
    "accent_soft": "rgba(134, 168, 145, 0.18)",
    "success": "#7DB38A",
    "warning": "#E0BD69",
    "error": "#E88484",
    "highlight": "#E8C66A",
}

SKADI_PALETTE = {
    "canvas": "#07111F",
    "surface": "#0B1725",
    "surface_elevated": "#102235",
    "surface_panel": "#0D1C2C",
    "surface_hover": "#162B3E",
    "surface_active": "#243647",
    "hairline": "#203448",
    "hairline_soft": "rgba(232, 228, 225, 0.08)",
    "hairline_strong": "#385066",
    "ink": "#F1EFEC",
    "body": "#D6D9DD",
    "muted": "#8E9CAA",
    "subtle": "#627384",
    "primary": "#C85C68",
    "on_primary": "#FFF8F6",
    "accent": "#D06B76",
    "accent_hover": "#E28B94",
    "accent_soft": "rgba(200, 92, 104, 0.18)",
    "success": "#79AA9A",
    "warning": "#D3A65D",
    "error": "#E77878",
    "highlight": "#D9A6AC",
}

THEME_OPTIONS = {
    "light": "浅色",
    "dark": "深色",
    "skadi": "浊心斯卡蒂 · 三形态",
}

BUILTIN_PALETTES = {
    "light": LIGHT_PALETTE,
    "dark": DARK_PALETTE,
    "skadi": SKADI_PALETTE,
}

THEME_PACK_BINDINGS = {
    "skadi": "corrupting-heart-skadi",
}

THEME_COLOR_KEYS = (
    "canvas",
    "surface",
    "surface_elevated",
    "surface_panel",
    "surface_hover",
    "surface_active",
    "hairline",
    "hairline_strong",
    "ink",
    "body",
    "muted",
    "subtle",
    "primary",
    "on_primary",
    "accent",
    "accent_hover",
    "success",
    "warning",
    "error",
    "highlight",
)

THEME_COLOR_LABELS = {
    "canvas": "窗口背景",
    "surface": "侧栏背景",
    "surface_elevated": "内容表面",
    "surface_panel": "浮层表面",
    "surface_hover": "悬停状态",
    "surface_active": "选中状态",
    "hairline": "分隔线",
    "hairline_strong": "强调边框",
    "ink": "主文字",
    "body": "正文文字",
    "muted": "次要文字",
    "subtle": "弱化文字",
    "primary": "主按钮",
    "on_primary": "主按钮文字",
    "accent": "强调色",
    "accent_hover": "强调色悬停",
    "success": "成功状态",
    "warning": "警告状态",
    "error": "错误状态",
    "highlight": "搜索高亮",
}

PALETTE = LIGHT_PALETTE
_HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


def theme_options() -> dict:
    options = dict(THEME_OPTIONS)
    try:
        from app.services.config_service import config_service
        custom = config_service.get("ui.custom_themes", {})
        if isinstance(custom, dict):
            for theme_id, value in custom.items():
                if isinstance(value, dict):
                    name = str(value.get("name", theme_id)).strip()
                    if name:
                        options[theme_id] = f"{name} · 自定义"
    except Exception:
        pass
    return options


def custom_themes() -> dict:
    try:
        from app.services.config_service import config_service
        value = config_service.get("ui.custom_themes", {})
        return deepcopy(value) if isinstance(value, dict) else {}
    except Exception:
        return {}


def validate_custom_theme(value: dict) -> tuple[bool, str]:
    if not isinstance(value, dict):
        return False, "主题数据必须是对象"
    name = str(value.get("name", "")).strip()
    palette = value.get("palette")
    if not name:
        return False, "主题名称不能为空"
    if not isinstance(palette, dict):
        return False, "主题缺少颜色配置"
    for key in THEME_COLOR_KEYS:
        color = palette.get(key)
        if not isinstance(color, str) or not _HEX_COLOR_RE.fullmatch(color):
            return False, f"{THEME_COLOR_LABELS[key]} 必须是 #RRGGBB 颜色"
    return True, ""


def save_custom_theme(theme_id: str, name: str, palette: dict) -> tuple[bool, str]:
    theme_id = re.sub(r"[^a-zA-Z0-9_-]+", "-", theme_id.strip()).strip("-").lower()
    if not theme_id:
        return False, "主题标识不能为空"
    if theme_id in BUILTIN_PALETTES:
        return False, "不能覆盖内置主题"
    value = {"name": name.strip(), "palette": deepcopy(palette)}
    valid, error = validate_custom_theme(value)
    if not valid:
        return False, error
    from app.services.config_service import config_service
    themes = custom_themes()
    themes[theme_id] = value
    config_service.set("ui.custom_themes", themes)
    return True, theme_id


def delete_custom_theme(theme_id: str) -> bool:
    themes = custom_themes()
    if theme_id not in themes:
        return False
    del themes[theme_id]
    from app.services.config_service import config_service
    config_service.set("ui.custom_themes", themes)
    return True


def palette_for_theme(theme_id: str, variant_id: str = "") -> dict:
    if theme_id in BUILTIN_PALETTES:
        merged = deepcopy(BUILTIN_PALETTES[theme_id])
    else:
        value = custom_themes().get(theme_id, {})
        palette = value.get("palette", {}) if isinstance(value, dict) else {}
        merged = deepcopy(DARK_PALETTE if _is_dark_palette(palette) else LIGHT_PALETTE)
        for key, color in palette.items():
            if key in merged and isinstance(color, str):
                merged[key] = color

    pack_id = THEME_PACK_BINDINGS.get(theme_id, "")
    if not pack_id:
        return merged
    pack = load_theme_pack(pack_id)
    variant = theme_pack_variant(pack_id, variant_id)
    for palette in (pack.get("base_palette", {}), variant.get("palette", {})):
        if not isinstance(palette, dict):
            continue
        for key, color in palette.items():
            if key in merged and isinstance(color, str):
                merged[key] = color
    return merged


def theme_variant_options(theme_id: str) -> dict:
    pack_id = THEME_PACK_BINDINGS.get(theme_id, "")
    if not pack_id:
        return {}
    return {
        item["id"]: item["name"]
        for item in theme_pack_variants(pack_id)
        if item.get("id") and item.get("name")
    }


def default_theme_variant(theme_id: str) -> str:
    pack_id = THEME_PACK_BINDINGS.get(theme_id, "")
    if not pack_id:
        return ""
    return str(load_theme_pack(pack_id).get("default_variant", ""))


def theme_variant_preference_key(theme_id: str) -> str:
    return f"ui_theme_variant:{theme_id}"


def current_theme_variant(theme_id: str = "") -> str:
    theme_id = theme_id or current_theme()
    options = theme_variant_options(theme_id)
    if not options:
        return ""
    default = default_theme_variant(theme_id)
    try:
        from app.services.state_service import state_service
        variant_id = state_service.get_preference(
            theme_variant_preference_key(theme_id),
            default,
        )
    except Exception:
        variant_id = default
    return variant_id if variant_id in options else default


def theme_asset(theme_id: str, variant_id: str = "") -> Path | None:
    pack_id = THEME_PACK_BINDINGS.get(theme_id, "")
    if not pack_id:
        return None
    return theme_pack_asset(pack_id, variant_id or default_theme_variant(theme_id))


def theme_display_label(theme_id: str, variant_id: str = "") -> str:
    pack_id = THEME_PACK_BINDINGS.get(theme_id, "")
    if not pack_id:
        return theme_options().get(theme_id, "主题")
    pack = load_theme_pack(pack_id)
    variant = theme_pack_variant(
        pack_id,
        variant_id or default_theme_variant(theme_id),
    )
    if not pack or not variant:
        return theme_options().get(theme_id, "主题")
    return f"{pack['name']} · {variant['name']}"


def _is_dark_palette(palette: dict) -> bool:
    color = str(palette.get("canvas", "#FFFFFF")).lstrip("#")
    if len(color) != 6:
        return False
    try:
        red, green, blue = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
    except ValueError:
        return False
    return red * 0.299 + green * 0.587 + blue * 0.114 < 128


def current_theme() -> str:
    try:
        from app.services.state_service import state_service
        theme = state_service.get_preference("ui_theme", "light")
    except Exception:
        theme = "light"
    return theme if theme in theme_options() else "light"


def current_palette() -> dict:
    theme_id = current_theme()
    return palette_for_theme(theme_id, current_theme_variant(theme_id))


def current_theme_asset() -> Path | None:
    theme_id = current_theme()
    return theme_asset(theme_id, current_theme_variant(theme_id))


def app_stylesheet() -> str:
    p = current_palette()
    return f"""
        QMainWindow, QDialog {{
            background: {p["canvas"]};
            color: {p["ink"]};
        }}
        QWidget#appShell {{
            background: {p["canvas"]};
        }}
        QWidget {{
            color: {p["body"]};
            font-family: "Segoe UI", "Microsoft YaHei UI", "Inter", sans-serif;
            font-size: 13px;
        }}
        QWidget#topBar {{
            background: {p["surface_panel"]};
            border-bottom: 1px solid {p["hairline"]};
        }}
        QWidget#commandBar, QWidget#sidebarCard, QWidget#editorCard {{
            background: {p["surface_panel"]};
            border: 1px solid {p["hairline"]};
            border-radius: 16px;
        }}
        QWidget#commandBar {{
            background: {p["surface_panel"]};
        }}
        QWidget#sidebarHeader, QWidget#editorToolbar, QWidget#sidebarActions {{
            background: transparent;
            border: none;
        }}
        QWidget#inlineControl, QWidget#metadataBar, QWidget#modeSegment {{
            background: {p["surface"]};
            border: 1px solid {p["hairline"]};
            border-radius: 11px;
        }}
        QWidget#themeColorGrid {{
            background: {p["surface_panel"]};
        }}
        QLabel {{
            color: {p["body"]};
            background: transparent;
        }}
        QLineEdit, QPlainTextEdit, QTextEdit, QTextBrowser, QComboBox, QSpinBox {{
            background: {p["surface_elevated"]};
            color: {p["ink"]};
            border: 1px solid {p["hairline"]};
            border-radius: 8px;
            selection-background-color: {p["accent"]};
            selection-color: {p["primary"]};
        }}
        QLineEdit {{
            min-height: 36px;
            padding: 0 12px;
            font-size: 14px;
        }}
        QLineEdit#globalSearch {{
            min-height: 42px;
            border-radius: 12px;
            padding-left: 16px;
            font-size: 14px;
            background: {p["surface"]};
        }}
        QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QTextBrowser:focus, QComboBox:focus {{
            border: 1px solid {p["accent"]};
            background: {p["surface_panel"]};
        }}
        QPlainTextEdit, QTextEdit, QTextBrowser {{
            padding: 12px;
            line-height: 1.5;
        }}
        QPlainTextEdit {{
            font-family: "Cascadia Code", "Consolas", "Microsoft YaHei UI", monospace;
            font-size: 13px;
        }}
        QPushButton {{
            background: {p["surface_panel"]};
            color: {p["body"]};
            border: 1px solid {p["hairline"]};
            border-radius: 10px;
            padding: 7px 12px;
            min-height: 22px;
            font-weight: 500;
        }}
        QPushButton:hover {{
            background: {p["surface_hover"]};
            border-color: {p["hairline_strong"]};
        }}
        QPushButton:pressed, QPushButton:checked {{
            background: {p["primary"]};
            color: {p["on_primary"]};
            border-color: {p["primary"]};
        }}
        QPushButton[role="primary"] {{
            background: {p["primary"]};
            color: {p["on_primary"]};
            border-color: {p["primary"]};
            font-weight: 600;
        }}
        QPushButton[role="primary"]:hover {{
            background: {p["accent_hover"]};
            border-color: {p["accent_hover"]};
        }}
        QPushButton[role="soft"] {{
            background: {p["surface"]};
            border-color: {p["hairline"]};
        }}
        QPushButton[role="soft"]:hover {{
            background: {p["surface_hover"]};
            border-color: {p["hairline_strong"]};
        }}
        QPushButton[role="toolbarToggle"] {{
            background: {p["surface"]};
            border-color: {p["hairline"]};
        }}
        QPushButton[role="toolbarToggle"]:checked {{
            color: {p["accent_hover"]};
            background: {p["accent_soft"]};
            border-color: {p["accent"]};
        }}
        QPushButton[role="icon"] {{
            min-height: 20px;
            padding: 2px;
            background: transparent;
            border-color: transparent;
            color: {p["muted"]};
            font-size: 18px;
        }}
        QPushButton[role="icon"]:hover {{
            background: {p["surface_hover"]};
            border-color: {p["hairline"]};
            color: {p["ink"]};
        }}
        QPushButton[role="sidebarPrimary"] {{
            color: {p["on_primary"]};
            background: {p["primary"]};
            border-color: {p["primary"]};
            font-weight: 600;
        }}
        QPushButton[role="sidebarPrimary"]:hover {{
            background: {p["accent_hover"]};
            border-color: {p["accent_hover"]};
        }}
        QPushButton[role="sidebarSoft"] {{
            color: {p["body"]};
            background: {p["surface"]};
            border-color: {p["hairline"]};
        }}
        QPushButton[role="segment"] {{
            min-height: 20px;
            padding: 5px 15px;
            color: {p["muted"]};
            background: transparent;
            border-color: transparent;
            border-radius: 8px;
        }}
        QPushButton[role="segment"]:hover {{
            color: {p["ink"]};
            background: {p["surface_hover"]};
        }}
        QPushButton[role="segment"]:checked {{
            color: {p["on_primary"]};
            background: {p["primary"]};
            border-color: {p["primary"]};
        }}
        QPushButton[role="chip"] {{
            min-height: 20px;
            padding: 4px 10px;
            color: {p["muted"]};
            background: {p["surface_panel"]};
            border-color: {p["hairline"]};
            border-radius: 9px;
            font-size: 12px;
        }}
        QPushButton[role="chip"]:checked {{
            color: {p["accent_hover"]};
            background: {p["accent_soft"]};
            border-color: {p["accent"]};
        }}
        QPushButton[role="danger"] {{
            color: {p["error"]};
        }}
        QPushButton[role="danger"]:hover {{
            background: {p["surface_hover"]};
            border-color: {p["error"]};
        }}
        QToolButton {{
            background: transparent;
            color: {p["body"]};
            border: 1px solid transparent;
            border-radius: 8px;
            padding: 6px;
        }}
        QToolButton:hover {{
            background: {p["surface_hover"]};
            border-color: {p["hairline"]};
        }}
        QPushButton:disabled {{
            background: {p["surface"]};
            color: {p["subtle"]};
            border-color: {p["hairline"]};
        }}
        QPushButton::menu-indicator {{
            width: 10px;
            padding-left: 4px;
        }}
        QTreeWidget, QListWidget {{
            background: {p["surface"]};
            color: {p["body"]};
            border: none;
            outline: none;
            alternate-background-color: {p["surface_elevated"]};
        }}
        QTreeWidget::item, QListWidget::item {{
            border-radius: 7px;
            padding: 7px 8px;
            margin: 1px 6px;
            color: {p["body"]};
        }}
        QTreeWidget::item:hover, QListWidget::item:hover {{
            background: {p["surface_hover"]};
            color: {p["ink"]};
        }}
        QTreeWidget::item:selected, QListWidget::item:selected {{
            background: {p["surface_active"]};
            color: {p["primary"]};
        }}
        QListWidget#settingsNav {{
            background: {p["surface"]};
            border: 1px solid {p["hairline"]};
            border-radius: 11px;
            padding: 6px;
        }}
        QListWidget#settingsNav::item {{
            padding: 9px 10px;
            margin: 2px 0;
            border-radius: 8px;
        }}
        QListWidget#settingsNav::item:selected {{
            background: {p["surface_active"]};
            color: {p["ink"]};
            border-left: 3px solid {p["accent"]};
        }}
        QStackedWidget {{
            background: {p["surface_panel"]};
            border: 1px solid {p["hairline"]};
            border-radius: 11px;
        }}
        QTreeWidget::branch, QListWidget::indicator {{
            background: transparent;
        }}
        QMenu {{
            background: {p["surface_panel"]};
            color: {p["ink"]};
            border: 1px solid {p["hairline"]};
            border-radius: 8px;
            padding: 6px;
        }}
        QMenu::item {{
            padding: 7px 28px 7px 10px;
            border-radius: 6px;
        }}
        QMenu::item:selected {{
            background: {p["surface_active"]};
            color: {p["primary"]};
        }}
        QMenu::separator {{
            height: 1px;
            background: {p["hairline"]};
            margin: 6px 4px;
        }}
        QSplitter::handle {{
            background: {p["canvas"]};
        }}
        QSplitter::handle:horizontal {{
            width: 10px;
        }}
        QSplitter::handle:vertical {{
            height: 1px;
        }}
        QStatusBar {{
            background: {p["canvas"]};
            color: {p["muted"]};
            border-top: none;
            padding: 3px 10px;
        }}
        QLabel#sidebarTitle {{
            color: {p["ink"]};
            font-size: 15px;
            font-weight: 700;
        }}
        QLabel#sidebarCaption, QLabel#sidebarFooter {{
            color: {p["muted"]};
            font-size: 11px;
        }}
        QLabel#dialogTitle {{
            color: {p["ink"]};
            font-size: 20px;
            font-weight: 700;
        }}
        QLabel#mutedText {{
            color: {p["muted"]};
            font-size: 12px;
        }}
        QToolTip {{
            background: {p["surface_elevated"]};
            color: {p["ink"]};
            border: 1px solid {p["hairline_strong"]};
            border-radius: 6px;
            padding: 5px 7px;
        }}
        QSlider::groove:horizontal {{
            height: 4px;
            background: {p["hairline"]};
            border-radius: 2px;
        }}
        QSlider::handle:horizontal {{
            background: {p["primary"]};
            border: 1px solid {p["hairline_strong"]};
            width: 14px;
            margin: -5px 0;
            border-radius: 7px;
        }}
        QTabWidget::pane {{
            border: 1px solid {p["hairline"]};
            border-radius: 8px;
            background: {p["surface_panel"]};
        }}
        QTabBar::tab {{
            background: transparent;
            color: {p["muted"]};
            padding: 8px 12px;
            border-radius: 7px;
            margin: 2px;
        }}
        QTabBar::tab:selected {{
            background: {p["surface_active"]};
            color: {p["ink"]};
        }}
        QGroupBox {{
            border: 1px solid {p["hairline"]};
            border-radius: 8px;
            margin-top: 10px;
            padding: 14px 10px 10px 10px;
            color: {p["ink"]};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 4px;
            color: {p["muted"]};
        }}
        QCheckBox, QRadioButton {{
            color: {p["body"]};
            spacing: 8px;
        }}
        QCheckBox::indicator, QRadioButton::indicator {{
            width: 14px;
            height: 14px;
            border: 1px solid {p["hairline_strong"]};
            background: {p["surface"]};
        }}
        QCheckBox::indicator {{
            border-radius: 4px;
        }}
        QRadioButton::indicator {{
            border-radius: 8px;
        }}
        QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
            background: {p["accent"]};
            border-color: {p["accent"]};
        }}
        QScrollArea {{
            background: {p["canvas"]};
            border: none;
        }}
        QScrollBar:vertical {{
            background: {p["surface"]};
            width: 10px;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background: {p["hairline_strong"]};
            border-radius: 5px;
            min-height: 28px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {p["subtle"]};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: transparent;
        }}
        QScrollBar:horizontal {{
            background: {p["surface"]};
            height: 10px;
            margin: 0;
        }}
        QScrollBar::handle:horizontal {{
            background: {p["hairline_strong"]};
            border-radius: 5px;
            min-width: 28px;
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0;
        }}
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
            background: transparent;
        }}
    """


def panel_stylesheet() -> str:
    p = current_palette()
    return f"""
        QWidget {{
            background: {p["canvas"]};
        }}
    """


def tree_stylesheet() -> str:
    p = current_palette()
    return f"""
        QTreeWidget {{
            border: none;
            outline: none;
            background: transparent;
            padding: 0;
        }}
        QTreeWidget::item {{
            background: transparent;
            border: none;
            padding: 0;
            margin: 0;
        }}
        QTreeWidget::item:selected {{
            background: transparent;
        }}
        QTreeWidget::item:hover {{
            background: transparent;
        }}
        QTreeWidget::branch {{
            background: transparent;
            width: 18px;
            border-image: none;
            image: none;
        }}
        QTreeWidget QScrollBar:vertical {{
            width: 7px;
            background: transparent;
        }}
        QTreeWidget QScrollBar::handle:vertical {{
            min-height: 32px;
            background: {p["hairline_strong"]};
            border-radius: 3px;
        }}
    """


def result_list_stylesheet() -> str:
    p = current_palette()
    return f"""
        QListWidget {{
            border: none;
            background: {p["surface"]};
            outline: none;
        }}
        QListWidget::item {{
            border-bottom: 1px solid {p["hairline"]};
            padding: 7px 8px;
            color: {p["body"]};
        }}
        QListWidget::item:selected {{
            background-color: {p["surface_active"]};
            color: {p["primary"]};
            border-left: 2px solid {p["accent"]};
        }}
        QListWidget::item:hover {{
            background-color: {p["surface_hover"]};
        }}
    """


def preview_stylesheet() -> str:
    p = current_palette()
    return f"""
        QPlainTextEdit, QTextEdit, QTextBrowser {{
            background: {p["surface_elevated"]};
            color: {p["body"]};
            border: 1px solid {p["hairline"]};
            border-radius: 13px;
            padding: 18px;
            font-size: 13px;
        }}
        QPlainTextEdit:focus, QTextEdit:focus, QTextBrowser:focus {{
            border-color: {p["hairline_strong"]};
        }}
    """


def muted_label_stylesheet() -> str:
    p = current_palette()
    return f"color: {p['muted']}; font-size: 12px; padding: 4px;"


def empty_label_stylesheet() -> str:
    p = current_palette()
    return f"""
        color: {p["muted"]};
        background: {p["surface"]};
        border: 1px dashed {p["hairline_strong"]};
        border-radius: 13px;
        padding: 40px;
        font-size: 14px;
    """


def highlight_html(text: str) -> str:
    p = current_palette()
    return (
        f"<span style='background:{p['highlight']};color:#000;"
        f"font-weight:600;border-radius:3px;padding:0 2px'>{text}</span>"
    )


def markdown_stylesheet(css: str) -> str:
    p = current_palette()
    return f"""
        <style>
            body {{
                background: {p["surface_elevated"]};
                color: {p["body"]};
                font-family: "Segoe UI", "Microsoft YaHei UI", Inter, sans-serif;
                line-height: 1.6;
                padding: 16px;
            }}
            h1, h2, h3, h4, h5, h6 {{
                color: {p["ink"]};
                margin-top: 24px;
                margin-bottom: 14px;
                font-weight: 600;
            }}
            h1 {{
                font-size: 1.7em;
                border-bottom: 1px solid {p["hairline"]};
                padding-bottom: 0.35em;
            }}
            h2 {{
                font-size: 1.35em;
                border-bottom: 1px solid {p["hairline"]};
                padding-bottom: 0.3em;
            }}
            a {{
                color: {p["accent_hover"]};
            }}
            code {{
                background-color: {p["surface_active"]};
                color: {p["ink"]};
                padding: 0.2em 0.4em;
                border-radius: 6px;
                font-size: 85%;
            }}
            pre {{
                background-color: {p["surface"]};
                color: {p["body"]};
                padding: 16px;
                overflow: auto;
                border: 1px solid {p["hairline"]};
                border-radius: 8px;
            }}
            pre code {{
                background-color: transparent;
                padding: 0;
            }}
            blockquote {{
                padding: 0 1em;
                color: {p["muted"]};
                border-left: 3px solid {p["accent"]};
                margin: 0;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 16px 0;
            }}
            th, td {{
                border: 1px solid {p["hairline"]};
                padding: 7px 12px;
            }}
            th {{
                background-color: {p["surface_active"]};
                color: {p["ink"]};
            }}
            ul, ol {{
                padding-left: 2em;
            }}
            li + li {{
                margin-top: 0.25em;
            }}
            hr {{
                height: 1px;
                padding: 0;
                margin: 24px 0;
                background-color: {p["hairline"]};
                border: 0;
            }}
            {css}
        </style>
    """
