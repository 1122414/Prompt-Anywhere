import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_imports():
    modules = [
        ("app.config", "Config"),
        ("app.constants", "AppConstants,Messages"),
        ("app.utils.singleton", "Singleton"),
        ("app.utils.json_store", "JsonFileStore"),
        ("app.services.file_service", "FileService,PromptFile"),
        ("app.services.search_service", "SearchService,SearchResult"),
        ("app.services.clipboard_service", "ClipboardService"),
        ("app.services.config_service", "ConfigService"),
        ("app.services.state_service", "StateService"),
        ("app.services.backup_service", "BackupService"),
        ("app.services.history_service", "HistoryService"),
        ("app.services.startup_service", "StartupService"),
        ("app.services.logging_service", "LoggingService"),
        ("app.services.export_service", "ExportService"),
        ("app.services.template_service", "TemplateService"),
        ("app.services.composer_service", "ComposerService"),
        ("app.services.pinyin_service", "PinyinService"),
        ("app.services.search_matcher", "SearchMatcher"),
        ("app.services.search_ranker", "SearchRanker"),
        ("app.services.semantic_search_service", "SemanticSearchService"),
        ("app.services.embedding_service", "EmbeddingService"),
        ("app.services.vector_store", "VectorStore"),
        ("app.services.builtin_template_service", "BuiltinTemplateService"),
        ("app.services.ai_template_service", "AITemplateService"),
        ("app.services.usage_service", "UsageService"),
        ("app.services.diagnostics_service", "DiagnosticsService"),
        ("app.services.knowledge_base_service", "KnowledgeBaseService"),
        ("app.services.tag_service", "TagService"),
        ("app.utils.markdown_utils", "MarkdownRenderer"),
    ]

    failed = []
    for module_name, symbols in modules:
        try:
            mod = __import__(module_name, fromlist=["dummy"])
            for sym in symbols.split(","):
                assert hasattr(mod, sym), f"{module_name} missing {sym}"
        except Exception as e:
            failed.append(f"{module_name}: {e}")

    return failed


def test_config():
    from app.config import Config
    Config._instance = None
    config = Config()

    props = [
        "app_name", "app_version", "hotkey", "always_on_top",
        "data_dir", "export_dir", "default_window_width", "default_window_height",
        "search_debounce_ms", "search_case_insensitive",
        "search_enable_pinyin", "search_enable_fuzzy",
        "semantic_search_enabled", "ai_template_enabled",
        "model_provider", "model_name",
    ]
    errors = []
    for prop in props:
        try:
            getattr(config, prop)
        except Exception as e:
            errors.append(f"config.{prop}: {e}")
    return errors


def test_singleton():
    from app.utils.singleton import Singleton

    class TestService(Singleton):
        def _init(self):
            self.value = 42

    a = TestService()
    b = TestService()
    assert a is b, "Singleton not returning same instance"
    assert a.value == 42, "Singleton _init not called"
    return []


def test_pure_functions():
    errors = []

    from app.utils.highlight_utils import highlight_text

    parts = highlight_text("中英翻译助手", "翻译")
    highlights = [p for p in parts if p["highlight"]]
    assert len(highlights) == 1, f"Expected 1 highlight, got {len(highlights)}"
    assert highlights[0]["text"] == "翻译", f"Expected '翻译', got '{highlights[0]['text']}'"

    parts = highlight_text("hello world", "")
    assert len(parts) == 1 and not parts[0]["highlight"], "Empty query should return no highlight"

    parts = highlight_text("test (special) chars", "(special)")
    highlights = [p for p in parts if p["highlight"]]
    assert len(highlights) == 1, "Special chars should work with re.escape"

    parts = highlight_text("", "test")
    assert len(parts) == 1 and not parts[0]["highlight"], "Empty text should return no highlight"

    parts = highlight_text("Case MATCH", "match")
    highlights = [p for p in parts if p["highlight"]]
    assert len(highlights) == 1, "Case insensitive should work"

    from app.ui.main_window import MainWindow
    mw = MainWindow.__new__(MainWindow)
    title = mw._extract_title_from_text("# 英文润色助手\n\n正文内容")
    assert title == "英文润色助手", f"Expected '英文润色助手', got '{title}'"

    title = mw._extract_title_from_text("请帮我把下面的文章总结成5个要点\n正文...")
    assert title == "请帮我把下面的文章总结成5个要点", f"Got '{title}'"

    title = mw._extract_title_from_text("A")
    assert title == "未命名 Prompt", f"Short title should be default, got '{title}'"

    title = mw._extract_title_from_text("- 列表项标题\n正文")
    assert title == "列表项标题", f"Got '{title}'"

    return errors


def run():
    print("=" * 60)
    print("Prompt Anywhere v0.3.0 功能验证测试")
    print("=" * 60)

    failed_count = 0

    print("\n[1/4] 模块导入测试...")
    import_errors = test_imports()
    if import_errors:
        failed_count += len(import_errors)
        for e in import_errors:
            print(f"  FAIL: {e}")
    else:
        print("  ALL 28 modules imported successfully")

    print("\n[2/4] 配置加载测试...")
    config_errors = test_config()
    if config_errors:
        failed_count += len(config_errors)
        for e in config_errors:
            print(f"  FAIL: {e}")
    else:
        print("  ALL config properties accessible")

    print("\n[3/4] 单例模式测试...")
    singleton_errors = test_singleton()
    if singleton_errors:
        failed_count += len(singleton_errors)
        for e in singleton_errors:
            print(f"  FAIL: {e}")
    else:
        print("  Singleton pattern working correctly")

    print("\n[v0.3] 纯函数测试...")
    pure_errors = test_pure_functions()
    if pure_errors:
        failed_count += len(pure_errors)
        for e in pure_errors:
            print(f"  FAIL: {e}")
    else:
        print("  highlight_text + extract_title passed")

    print("\n[4/4] 单元测试套件...")
    test_files = [
        "test_functional.py",
        "test_product_services.py",
        "test_template_composer.py",
        "test_upgrade_features.py",
    ]
    for tf in test_files:
        loader = unittest.TestLoader()
        suite = loader.discover(
            str(Path(__file__).parent), pattern=tf
        )
        runner = unittest.TextTestRunner(verbosity=0)
        result = runner.run(suite)
        status = "OK" if result.wasSuccessful() else f"FAIL ({len(result.failures)} failures, {len(result.errors)} errors)"
        if not result.wasSuccessful():
            failed_count += len(result.failures) + len(result.errors)
        print(f"  {tf}: {status}")

    print("\n" + "=" * 60)
    if failed_count == 0:
        print("ALL TESTS PASSED")
        print("=" * 60)
        return 0
    else:
        print(f"{failed_count} FAILURES DETECTED")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(run())
