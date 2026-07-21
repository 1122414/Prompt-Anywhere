import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import Config
from app.services.file_service import FileService, PromptFile
from app.services.search_service import SearchService
from app.services.clipboard_service import ClipboardService
from app.utils.markdown_utils import MarkdownRenderer


class TestConfig(unittest.TestCase):
    _env_keys = [
        "APP_NAME", "APP_VERSION", "GLOBAL_HOTKEY", "ALWAYS_ON_TOP",
        "START_MINIMIZED", "DATA_DIR", "EXPORT_DIR", "WINDOW_X",
        "WINDOW_Y", "WINDOW_WIDTH", "WINDOW_HEIGHT", "DEFAULT_MODE",
        "DEFAULT_WINDOW_WIDTH", "DEFAULT_WINDOW_HEIGHT",
        "FILE_ENCODING", "PYGMENTS_STYLE", "SEARCH_CASE_INSENSITIVE",
        "LOG_LEVEL", "ENABLE_FILE_WATCHER",
        "MODEL_PROVIDER", "MODEL_NAME", "MODEL_API_KEY",
        "MODEL_BASE_URL", "MODEL_TEMPERATURE",
    ]

    def setUp(self):
        self._saved_env = {}
        for key in self._env_keys:
            self._saved_env[key] = os.environ.get(key)
            if key in os.environ:
                del os.environ[key]

        Config._instance = None
        from app.services.config_service import config_service
        self._saved_user_config = config_service._user_config
        config_service._user_config = {}
        from app.services.state_service import StateService
        StateService._instance = None
        self.config = Config()
        self.config._config_data = {
            "app": {"hotkey": "ctrl+shift+p", "always_on_top": False},
            "storage": {"data_dir": "./custom_data"},
            "ui": {"default_window_width": 1200},
            "model": {"provider": "openai", "name": "gpt-4"},
        }

    def tearDown(self):
        for key, value in self._saved_env.items():
            if value is not None:
                os.environ[key] = value
            elif key in os.environ:
                del os.environ[key]
        Config._instance = None
        from app.services.config_service import config_service
        config_service._user_config = self._saved_user_config
        from app.services.state_service import StateService
        StateService._instance = None

    def test_yaml_fallback_hotkey(self):
        self.assertEqual(self.config.hotkey, "ctrl+shift+p")

    def test_yaml_fallback_always_on_top(self):
        self.assertEqual(self.config.always_on_top, False)

    def test_yaml_fallback_window_width(self):
        self.assertEqual(self.config.window_width, 1200)

    def test_yaml_fallback_model_provider(self):
        self.assertEqual(self.config.model_provider, "openai")

    def test_yaml_fallback_model_name(self):
        self.assertEqual(self.config.model_name, "gpt-4")

    def test_env_overrides_yaml(self):
        os.environ["GLOBAL_HOTKEY"] = "ctrl+alt+x"
        Config._instance = None
        config2 = Config()
        config2._config_data = self.config._config_data
        self.assertEqual(config2.hotkey, "ctrl+alt+x")
        del os.environ["GLOBAL_HOTKEY"]
        Config._instance = None


class TestFileService(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.data_dir = self.test_dir / "data"
        self.data_dir.mkdir()

        os.environ["DATA_DIR"] = str(self.data_dir)
        Config._instance = None
        FileService._instance = None
        self.config = Config()

        self.file_service = FileService()
        self.file_service._ensure_data_dir()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
        if "DATA_DIR" in os.environ:
            del os.environ["DATA_DIR"]
        Config._instance = None
        FileService._instance = None

    def test_create_category(self):
        result = self.file_service.create_category("Coding")
        self.assertTrue(result)
        self.assertTrue((self.data_dir / "Coding").exists())

    def test_create_prompt(self):
        self.file_service.create_category("Coding")
        prompt = self.file_service.create_prompt("Coding", "测试", ".md", "# 测试内容")
        self.assertIsNotNone(prompt)
        self.assertTrue((self.data_dir / "Coding" / "测试.md").exists())
        self.assertEqual(prompt.read_content(), "# 测试内容")

    def test_get_categories(self):
        self.file_service.create_category("A")
        self.file_service.create_category("B")
        cats = self.file_service.get_categories()
        self.assertEqual(cats, ["A", "B"])

    def test_get_prompts(self):
        self.file_service.create_category("Cat")
        self.file_service.create_prompt("Cat", "p1", ".md")
        self.file_service.create_prompt("Cat", "p2", ".txt")
        prompts = self.file_service.get_prompts("Cat")
        self.assertEqual(len(prompts), 2)

    def test_rename_category(self):
        self.file_service.create_category("Old")
        result = self.file_service.rename_category("Old", "New")
        self.assertTrue(result)
        self.assertTrue((self.data_dir / "New").exists())

    def test_delete_category(self):
        self.file_service.create_category("ToDelete")
        result = self.file_service.delete_category("ToDelete")
        self.assertTrue(result)
        self.assertFalse((self.data_dir / "ToDelete").exists())

    def test_rename_prompt(self):
        self.file_service.create_category("Cat")
        prompt = self.file_service.create_prompt("Cat", "Old", ".md")
        result = self.file_service.rename_prompt(prompt, "New")
        self.assertTrue(result)
        self.assertTrue((self.data_dir / "Cat" / "New.md").exists())

    def test_delete_prompt(self):
        self.file_service.create_category("Cat")
        prompt = self.file_service.create_prompt("Cat", "ToDelete", ".md")
        result = self.file_service.delete_prompt(prompt)
        self.assertTrue(result)
        self.assertFalse((self.data_dir / "Cat" / "ToDelete.md").exists())


class TestSearchService(unittest.TestCase):
    def setUp(self):
        self.search_service = SearchService()
        SearchService._instance = None
        self.search_service = SearchService()
        self.test_dir = Path(tempfile.mkdtemp())
        self.data_dir = self.test_dir / "data"
        self.data_dir.mkdir()

        os.environ["DATA_DIR"] = str(self.data_dir)
        Config._instance = None
        FileService._instance = None
        self.config = Config()

        self.file_service = FileService()
        self.file_service.create_category("Test")
        self.p1 = self.file_service.create_prompt("Test", "代码审查", ".md", "审查代码质量")
        self.p2 = self.file_service.create_prompt("Test", "代码精简", ".md", "精简代码逻辑")
        self.p3 = self.file_service.create_prompt("Test", "面试", ".md", "面试技巧")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
        if "DATA_DIR" in os.environ:
            del os.environ["DATA_DIR"]
        Config._instance = None
        FileService._instance = None
        SearchService._instance = None

    def test_search_by_name(self):
        self.search_service.rebuild_index()
        results = self.search_service.search("代码")
        self.assertEqual(len(results), 2)
        names = [r.filename for r in results]
        self.assertIn("代码审查", names)
        self.assertIn("代码精简", names)

    def test_search_by_content(self):
        self.search_service.rebuild_index()
        results = self.search_service.search("面试")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].filename, "面试")

    def test_search_empty_keyword(self):
        self.search_service.rebuild_index()
        results = self.search_service.search("")
        self.assertEqual(len(results), 3)


class TestMarkdownRenderer(unittest.TestCase):
    def setUp(self):
        self.renderer = MarkdownRenderer()

    def test_render_basic(self):
        text = "# Hello\n\nWorld"
        html = self.renderer.render(text)
        self.assertIn("Hello", html)
        self.assertIn("World", html)

    def test_render_code_block(self):
        text = "```python\nprint(1)\n```"
        html = self.renderer.render(text)
        self.assertIn("print", html)

    def test_render_table(self):
        text = "| A | B |\n|---|---|\n| 1 | 2 |"
        html = self.renderer.render(text)
        self.assertIn("table", html)


class TestClipboardService(unittest.TestCase):
    def test_singleton(self):
        from app.services.clipboard_service import clipboard_service
        from app.services.clipboard_service import ClipboardService
        cs = ClipboardService()
        self.assertEqual(cs, clipboard_service)


class TestThemeSystem(unittest.TestCase):
    def setUp(self):
        from app.services.config_service import config_service
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_service = config_service
        self.original_path = config_service._config_path
        self.original_user_config = config_service._user_config
        config_service._config_path = self.temp_dir / "app_config.json"
        config_service._user_config = {}

    def tearDown(self):
        self.config_service._config_path = self.original_path
        self.config_service._user_config = self.original_user_config
        shutil.rmtree(self.temp_dir)

    def test_skadi_theme_has_complete_palette(self):
        from app.ui.theme import THEME_COLOR_KEYS, palette_for_theme
        palette = palette_for_theme("skadi")
        for key in THEME_COLOR_KEYS:
            self.assertIn(key, palette)
        self.assertEqual(palette["canvas"], "#07111F")

    def test_skadi_theme_pack_has_three_valid_variants(self):
        from app.ui.theme import theme_asset, theme_variant_options
        from app.ui.theme_pack import load_theme_pack

        pack = load_theme_pack("corrupting-heart-skadi")
        self.assertEqual(pack["default_variant"], "abyssal-omen")
        self.assertEqual(len(pack["variants"]), 3)
        self.assertEqual(
            list(theme_variant_options("skadi")),
            ["abyssal-omen", "crimson-coronation", "serene-tide"],
        )
        for variant_id in theme_variant_options("skadi"):
            asset = theme_asset("skadi", variant_id)
            self.assertIsNotNone(asset)
            self.assertTrue(asset.exists())

    def test_skadi_variants_apply_distinct_palette_overrides(self):
        from app.ui.theme import palette_for_theme

        abyssal = palette_for_theme("skadi", "abyssal-omen")
        crimson = palette_for_theme("skadi", "crimson-coronation")
        serene = palette_for_theme("skadi", "serene-tide")
        self.assertEqual(abyssal["accent"], "#35C7DD")
        self.assertEqual(crimson["canvas"], "#0B0E1E")
        self.assertEqual(serene["primary"], "#75BFB9")
        self.assertEqual(serene["on_primary"], "#061318")

    def test_theme_pack_loader_rejects_path_traversal(self):
        from app.ui.theme_pack import theme_pack_manifest_path

        self.assertIsNone(theme_pack_manifest_path("../corrupting-heart-skadi"))

    def test_custom_theme_round_trip(self):
        from app.ui.theme import (
            delete_custom_theme,
            palette_for_theme,
            save_custom_theme,
            theme_options,
        )
        palette = palette_for_theme("dark")
        palette["accent"] = "#3366FF"
        success, theme_id = save_custom_theme("Ocean Blue", "海风蓝", palette)
        self.assertTrue(success)
        self.assertEqual(theme_id, "ocean-blue")
        self.assertIn("ocean-blue", theme_options())
        self.assertEqual(palette_for_theme("ocean-blue")["accent"], "#3366FF")
        self.assertTrue(delete_custom_theme("ocean-blue"))

    def test_custom_theme_rejects_invalid_color(self):
        from app.ui.theme import palette_for_theme, validate_custom_theme
        palette = palette_for_theme("light")
        palette["accent"] = "blue"
        valid, error = validate_custom_theme({"name": "错误主题", "palette": palette})
        self.assertFalse(valid)
        self.assertIn("#RRGGBB", error)

    def test_user_settings_feed_runtime_config(self):
        from app.config import config
        custom_data = self.temp_dir / "prompts"
        self.config_service.set("storage.data_dir", str(custom_data))
        self.config_service.set("model.name", "user-model")
        self.config_service.set("window.opacity", 0.82)
        self.assertEqual(config.data_dir, custom_data.resolve())
        self.assertEqual(config.model_name, "user-model")
        self.assertEqual(config.default_window_opacity, 0.82)



class TestUIInitialization(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def test_editor_panel_constructs_without_early_event_filter_crash(self):
        from app.ui.panels import EditorPanel
        panel = EditorPanel()
        self.assertIsNotNone(panel.editor)
        self.assertIsNotNone(panel.preview)
        panel.deleteLater()

    def test_settings_and_theme_editor_construct(self):
        from app.ui.settings_dialog import SettingsDialog
        from app.ui.theme import palette_for_theme
        from app.ui.theme_editor_dialog import ThemeEditorDialog
        settings = SettingsDialog()
        editor = ThemeEditorDialog("测试主题", palette_for_theme("skadi"))
        self.assertEqual(settings.settings_stack.count(), 11)
        settings.theme_combo.setCurrentIndex(settings.theme_combo.findData("skadi"))
        self.assertEqual(settings.theme_variant_combo.count(), 3)
        self.assertFalse(settings.theme_preview._pixmap.isNull())
        self.assertEqual(len(editor.theme_data()[2]), len(palette_for_theme("skadi")))
        settings.deleteLater()
        editor.deleteLater()

    def test_sidebar_collapse_uses_parent_splitter(self):
        from PySide6.QtWidgets import QSplitter, QWidget
        from app.ui.tree_panel import SidebarItemDelegate, TreePanel
        splitter = QSplitter()
        panel = TreePanel()
        splitter.addWidget(panel)
        splitter.addWidget(QWidget())
        self.assertEqual(panel.objectName(), "sidebarCard")
        self.assertIsInstance(panel.tree.itemDelegate(), SidebarItemDelegate)
        self.assertTrue(panel.new_prompt_btn.isVisibleTo(panel))
        panel._toggle_collapse()
        self.assertTrue(panel._collapsed)
        self.assertEqual(panel.maximumWidth(), 40)
        self.assertTrue(panel.tree.isHidden())
        self.assertTrue(panel.quick_actions_host.isHidden())
        panel._toggle_collapse()
        self.assertFalse(panel._collapsed)
        self.assertFalse(panel.tree.isHidden())
        splitter.deleteLater()

    def test_quick_window_starts_with_search_empty_state(self):
        from app.ui.quick_window import QuickWindow
        window = QuickWindow()
        self.assertFalse(window.search_result_panel.isVisible())
        self.assertFalse(window.empty_state.isHidden())
        window.deleteLater()


def run_tests():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestFileService))
    suite.addTests(loader.loadTestsFromTestCase(TestSearchService))
    suite.addTests(loader.loadTestsFromTestCase(TestMarkdownRenderer))
    suite.addTests(loader.loadTestsFromTestCase(TestClipboardService))
    suite.addTests(loader.loadTestsFromTestCase(TestThemeSystem))
    suite.addTests(loader.loadTestsFromTestCase(TestUIInitialization))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
