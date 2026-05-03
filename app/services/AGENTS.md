# app/services — Business Logic

**25 files.** All singleton services, instantiated at module level.

## OVERVIEW

Core business logic layer. Each file exports one `ServiceClass` + one module-level `service_name = ServiceClass()` instance. Services manage files, search, templates, composer, clipboard, state, backup, and more.

## STRUCTURE

```
services/
├── file_service.py            # PromptFile dataclass, file CRUD, file iteration
├── search_service.py          # SearchIndex + SearchWorker (QThread), @dataclass result types
├── search_matcher.py          # Exact, fuzzy, pinyin matching helpers
├── search_ranker.py           # Multi-factor search result scoring
├── semantic_search_service.py # Embedding-based search (optional, gated by config)
├── pinyin_service.py          # Chinese pinyin + initials generation
├── template_service.py        # `{{变量名}}` extraction + variable token generation
├── composer_service.py        # Multi-file prompt composition (add/remove/reorder/build)
├── clipboard_service.py       # Clipboard copy (raw Markdown/text)
├── config_service.py          # User config (app_config.json) + env vars
├── state_service.py           # Runtime state (app_state.json) persistence
├── backup_service.py          # Auto-backup + restore
├── history_service.py         # File version history (pre-save snapshots)
├── startup_service.py         # First-run setup (dirs, config, builtin templates)
├── logging_service.py         # File logging + global exception hook
├── diagnostics_service.py     # Diagnostic data export
├── knowledge_base_service.py  # KB index generation + query
├── tag_service.py             # Prompt tagging
├── usage_service.py           # Usage statistics tracking
├── export_service.py          # Prompt export
├── builtin_template_service.py # Built-in template management + import
├── ai_template_service.py     # AI + rule-based template variable detection
├── embedding_service.py       # Text embedding generation (optional)
├── vector_store.py            # ChromaDB-backed vector store (optional)
└── __init__.py                # Empty
```

## WHERE TO LOOK

| Task | File | Key Symbol |
|------|------|------------|
| File operations | `file_service.py` | `file_service`, `PromptFile` dataclass |
| Search | `search_service.py` | `search_service`, `SearchWorker` (QThread), `SearchResult` |
| Pinyin search | `pinyin_service.py` | `pinyin_service` |
| Fuzzy matching | `search_matcher.py` | `search_matcher`, `FuzzyMatchResult` |
| Template variables | `template_service.py` | `template_service` |
| Prompt composition | `composer_service.py` | `composer_service` |
| Clipboard | `clipboard_service.py` | `clipboard_service` |
| User config | `config_service.py` | `config_service` |
| Runtime state | `state_service.py` | `state_service` |
| Backup | `backup_service.py` | `backup_service` |
| Diagnostics | `diagnostics_service.py` | `diagnostics_service` |
| KB index | `knowledge_base_service.py` | `knowledge_base_service` |
| Tags | `tag_service.py` | `tag_service` |
| Usage stats | `usage_service.py` | `usage_service` |
| AI template | `ai_template_service.py` | `ai_template_service`, `TemplateVariable` |
| Embeddings | `embedding_service.py` | `embedding_service` (optional) |
| Vector store | `vector_store.py` | `vector_store` (optional, ChromaDB) |
| Export | `export_service.py` | `export_service` |

## CONVENTIONS

- **Singleton**: `__new__` + `_instance` class var. Instantiate at module bottom: `file_service = FileService()`.
- **Logger**: `logger = logging.getLogger(__name__)` at module level, between stdlib and third-party imports.
- **Config access**: Always through `from app.config import config` — never `os.getenv()` directly.
- **Deferred imports**: Import other services inside methods (not at module top) to avoid circular deps.
- **Error handling**: `except Exception as e:` with `logger.warning(f"...{e}")`. No bare `except:`.
- **Data containers**: `@dataclass` for `SearchResult`, `PromptFileIndexItem`, `FuzzyMatchResult`, `TemplateVariable`.
- **File I/O**: Always `encoding="utf-8"` explicit.

## ANTI-PATTERNS

- Do NOT block UI thread — use QThread-based SearchWorker for search
- Do NOT read config via `os.getenv()` in services — all config through `config.py`
- Do NOT read full file on every keystroke — use in-memory SearchIndex
- Do NOT add pytest or mock to tests
- Do NOT force YAML metadata or structured PromptItem formats
