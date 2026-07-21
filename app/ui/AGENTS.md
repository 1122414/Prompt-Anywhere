# app/ui — PySide6 Widgets

All UI components using PySide6/Qt.

## OVERVIEW

Desktop GUI layer: windows, dialogs, panels, tray. Widgets communicate via typed `Signal()` from PySide6.QtCore. Chinese-language UI strings. No CSS framework — stylesheet strings inline or in QSS files.

## STRUCTURE

```
ui/
├── main_window.py         # MainWindow: tree panel + editor panel + search. Win32 hotkey via ctypes.
├── quick_window.py        # QuickWindow: popup search with QTimer debounce
├── tree_panel.py          # TreePanel: file tree with drag-drop, context menus
├── panels.py              # EditorPanel: edit/preview modes, markdown rendering, template actions
├── search_result_panel.py # SearchResultPanel: result list + preview pane + keyboard nav
├── search_popup.py        # SearchPopupWindow: standalone search result window (StaysOnTop)
├── composer_dialog.py     # ComposerDialog: multi-file prompt composition (splitter layout)
├── dialogs.py             # CategoryDialog, TemplateDialog, VariableNameDialog, SearchDialog
├── settings_dialog.py     # SettingsDialog: 11-page sidebar navigation (appearance, data, model, etc.)
├── theme.py               # Built-in/custom palettes, QSS, validation, theme persistence helpers
├── theme_pack.py          # Manifest-driven reusable background theme pack loader
├── theme_editor_dialog.py # Visual custom-theme editor with live preview and JSON round-trip
├── theme_widgets.py       # Theme-aware header, artwork rendering, and variant preview
├── ai_template_dialog.py  # AITemplateDialog: AI/rule/hybrid variable detection
├── tray.py                # TrayManager: system tray icon + context menu
└── __init__.py            # Empty
```

## WHERE TO LOOK

| Task | File | Key Class |
|------|------|-----------|
| Main app window | `main_window.py` | `MainWindow` (QMainWindow) |
| Quick search popup | `quick_window.py` | `QuickWindow` (QMainWindow) |
| File tree | `tree_panel.py` | `TreePanel` (QWidget) |
| Editor/preview | `panels.py` | `EditorPanel` (QWidget) |
| Search results | `search_result_panel.py` | `SearchResultPanel` (QWidget) |
| Search popup window | `search_popup.py` | `SearchPopupWindow` (QMainWindow) |
| Composer | `composer_dialog.py` | `ComposerDialog` (QDialog) |
| Dialogs | `dialogs.py` | `CategoryDialog`, `TemplateDialog`, etc. |
| Settings | `settings_dialog.py` | `SettingsDialog` (QDialog) |
| Theme system | `theme.py` + `theme_pack.py` + `theme_editor_dialog.py` | Palettes, background packs, editor, import/export |
| AI template | `ai_template_dialog.py` | `AITemplateDialog` (QDialog) |
| System tray | `tray.py` | `TrayManager` (QSystemTrayIcon) |

## CONVENTIONS

- **Widget setup**: `_setup_ui()` method called from `__init__`, builds widget tree, connects signals.
- **Signals**: Typed `Signal(str)` for string payloads, `Signal()` for void. Named semantically: `result_selected`, `escape_pressed`, `open_main_requested`.
- **Debounce**: `QTimer(self)` with `.setSingleShot(True)` for search input debouncing.
- **Event filtering**: `installEventFilter(self)` + `eventFilter()` override for custom key handling (Ctrl+V image paste).
- **Context menus**: `setContextMenuPolicy(Qt.CustomContextMenu)` + `customContextMenuRequested` signal.
- **StaysOnTop**: Quick windows use `Qt.WindowStaysOnTopHint | Qt.Tool`.
- **Chinese UI**: All user-facing strings are Chinese — button labels, placeholder text, dialog titles.
- **Logging**: `logger = logging.getLogger(__name__)` at module level.
- **Imports**: Absolute only. Deferred imports inside methods for circular dep avoidance.

## ANTI-PATTERNS

- Do NOT block main thread — use QThread for long operations
- Do NOT use `print()` — use `logging`
- Do NOT hardcode paths — use `config.data_dir` / `config.export_dir`
- Do NOT use `pywin32` unless pynput truly cannot fix the issue
- Do NOT change "copy = raw Markdown/text" behavior
