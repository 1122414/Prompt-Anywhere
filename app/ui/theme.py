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
    "muted": "#9B968B",
    "subtle": "#B9B3A8",
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

THEME_OPTIONS = {
    "light": "浅色",
    "dark": "深色",
}

PALETTE = LIGHT_PALETTE


def current_theme() -> str:
    try:
        from app.services.state_service import state_service
        theme = state_service.get_preference("ui_theme", "light")
    except Exception:
        theme = "light"
    return theme if theme in THEME_OPTIONS else "light"


def current_palette() -> dict:
    if current_theme() == "dark":
        return DARK_PALETTE
    return LIGHT_PALETTE


def app_stylesheet() -> str:
    p = current_palette()
    return f"""
        QMainWindow, QDialog {{
            background: {p["canvas"]};
            color: {p["ink"]};
        }}
        QWidget {{
            color: {p["body"]};
            font-family: "Segoe UI", "Microsoft YaHei UI", "Inter", sans-serif;
            font-size: 13px;
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
            min-height: 34px;
            padding: 0 12px;
            font-size: 14px;
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
            border-radius: 8px;
            padding: 7px 12px;
            min-height: 20px;
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
            background: {p["hairline"]};
        }}
        QSplitter::handle:horizontal {{
            width: 1px;
        }}
        QSplitter::handle:vertical {{
            height: 1px;
        }}
        QStatusBar {{
            background: {p["surface_panel"]};
            color: {p["muted"]};
            border-top: 1px solid {p["hairline"]};
            padding: 2px 8px;
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
            background: {p["surface"]};
        }}
        QTreeWidget::item {{
            padding: 7px 8px;
            border-radius: 7px;
            margin: 1px 6px;
            color: {p["body"]};
        }}
        QTreeWidget::item:selected {{
            background: {p["surface_active"]};
            color: {p["primary"]};
        }}
        QTreeWidget::item:hover {{
            background: {p["surface_hover"]};
            color: {p["ink"]};
        }}
        QTreeWidget::branch {{
            background: transparent;
            width: 22px;
            border-image: none;
            image: none;
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
            border-radius: 8px;
            padding: 12px;
            font-size: 13px;
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
        border-radius: 8px;
        padding: 40px;
        font-size: 13px;
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
