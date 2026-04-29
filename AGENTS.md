# PROJECT KNOWLEDGE BASE

**Generated:** 2026-04-29
**Commit:** 82ec309
**Branch:** main

## OVERVIEW

PySide6 desktop app for managing prompts globally. Hotkey-triggered prompt manager with search, clipboard copy, and markdown rendering. Python 3.11+, no web backend.

## STRUCTURE

```
Prompt-Anywhere/
├── app/
│   ├── main.py          # Entry point: QApplication + MainWindow + QuickWindow
│   ├── config.py        # Singleton Config: YAML + env var override
│   ├── constants.py     # App-wide constants and UI messages (Chinese)
│   ├── ui/              # PySide6 widgets (windows, dialogs, panels)
│   ├── services/        # Business logic (file, search, clipboard, state, export)
│   ├── providers/       # Storage abstractions (ABC pattern, mostly stubs)
│   └── utils/           # Helpers (markdown, syntax highlighting, images)
├── tests/               # unittest-based functional tests
├── data/                # User prompts (gitignored)
├── plan_/               # Planning docs (Chinese, date-based subdirs)
├── config.yaml          # App config (hotkey, UI, storage, model)
├── requirements.txt     # PySide6, pynput, markdown, PyYAML, dotenv, send2trash
└── app_state.json       # Runtime state (gitignored)
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add UI component | `app/ui/` | PySide6 widgets, follow existing patterns |
| Add service | `app/services/` | Singleton pattern, instantiate at module level |
| Change config | `config.yaml` + `app/config.py` | Env vars override YAML |
| Add file type support | `config.yaml` → `supported_extensions` | Default: `.md,.txt` |
| Modify hotkey | `config.yaml` → `app.hotkey` | Uses pynput GlobalHotKeys |
| Run tests | `python tests/test_functional.py` | unittest, no pytest config |

## CONVENTIONS

- **Singleton pattern**: All services use `__new__` with `_instance` class var. Instantiate at module bottom: `service = Service()`
- **Config priority**: user pref (app_state.json) > env var > YAML > hardcoded default (for: copy_auto_hide, esc_hide_enabled, copy_hide_delay_ms, search_selected_bg_color)
- **Config priority (most properties)**: env var > YAML > hardcoded default
- **Chinese UI**: All user-facing strings in `app/constants.py` are Chinese. Some inline strings in UI files.
- **Logging**: `logging.getLogger(__name__)` per module, format: `%(asctime)s [%(levelname)s] %(name)s: %(message)s`
- **Path handling**: Use `pathlib.Path`, resolve relative to `config.data_dir`. Display with `.as_posix()` or `.replace("\\", "/")`
- **Qt signals**: Use `Signal()` from PySide6.QtCore for inter-widget communication
- **Imports**: Absolute only (`from app.config import config`). Deferred imports for circular deps or lazy loading.
- **Quotes**: Double quotes `"` everywhere (no single quotes)
- **No docstrings**: Entire codebase has zero docstrings
- **Type hints**: On public methods, absent on private
- **Git commits**: Conventional Commits style (`fix:`, `feat:`, `chore:`), descriptions often Chinese

## ANTI-PATTERNS (THIS PROJECT)

- Do NOT add new dependencies without checking if existing ones cover the need
- Do NOT commit `data/`, `exports/`, `app_state.json`, or `__pycache__/`
- Do NOT use `print()` — use `logging.getLogger(__name__)`
- Do NOT hardcode paths — use `config.data_dir` / `config.export_dir`
- Do NOT implement stub classes in `app/providers/` (EmbeddingSearchProvider, VectorSearchProvider, AISearchProvider, DatabasePromptStorage, CloudPromptStorage, ChatGPTImportProvider, NotionImportProvider, WebImportProvider, FutureAIService)
- Do NOT add LLM integration, semantic search, vector databases, cloud sync, web UI, browser extensions, login/permission systems
- Do NOT force YAML metadata or structured PromptItem formats on users
- Do NOT change `data/` folder storage rules or "copy = raw Markdown/text" behavior
- Do NOT read config via `os.getenv()` in services — all config access through `config.py`
- Do NOT block UI thread for search — use QThread-based SearchWorker
- Do NOT read full file on every keystroke — use in-memory SearchIndex
- Do NOT use `pywin32` unless pynput truly cannot fix the issue

## COMMANDS

```bash
# Run app
python -m app.main

# Run tests
python tests/test_functional.py

# Install dependencies
pip install -r requirements.txt
```

## TESTING

- **Framework**: stdlib `unittest` only — do NOT introduce pytest or mock
- **All tests in single file**: `tests/test_functional.py` — add new test classes there
- **Singleton reset**: Always set `ClassName._instance = None` in setUp/tearDown
- **Isolation**: Use `tempfile.mkdtemp()` + env var manipulation + `shutil.rmtree()`
- **No mocking**: Tests use real implementations against temp filesystem
- **Manual UI tests**: Documented in `tests/调试测试指南.md`

## NOTES

- No CI/CD configured — manual builds only
- No pyproject.toml or setup.py — run directly, not packaged
- `app/providers/` contains ABC stubs for future storage backends (Database, Cloud) — mostly unimplemented
- Window state persists to `app_state.json` (position, size, opacity, last selected file)
- `.env` is committed to repo (contains API key placeholders, currently empty)
- `config.yaml` is writable at runtime (folder icons stored there)
- Tests in `test_functional.py` reference non-existent methods (`SearchService.search()`, `config.window_width`) — may fail
