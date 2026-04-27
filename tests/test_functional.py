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


class TestFileService(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.data_dir = self.test_dir / "data"
        self.data_dir.mkdir()

        Config._instance = None
        self.config = Config()
        self.config._config_data = {"storage": {"data_dir": str(self.data_dir)}}

        self.file_service = FileService()
        self.file_service._ensure_data_dir()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
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
        self.test_dir = Path(tempfile.mkdtemp())
        self.data_dir = self.test_dir / "data"
        self.data_dir.mkdir()

        Config._instance = None
        self.config = Config()
        self.config._config_data = {"storage": {"data_dir": str(self.data_dir)}}

        self.file_service = FileService()
        self.file_service.create_category("Test")
        self.p1 = self.file_service.create_prompt("Test", "代码审查", ".md", "审查代码质量")
        self.p2 = self.file_service.create_prompt("Test", "代码精简", ".md", "精简代码逻辑")
        self.p3 = self.file_service.create_prompt("Test", "面试", ".md", "面试技巧")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
        Config._instance = None
        FileService._instance = None

    def test_search_by_name(self):
        prompts = [self.p1, self.p2, self.p3]
        results = self.search_service.search("代码", prompts)
        self.assertEqual(len(results), 2)
        names = [p.name for p in results]
        self.assertIn("代码审查", names)
        self.assertIn("代码精简", names)

    def test_search_by_content(self):
        prompts = [self.p1, self.p2, self.p3]
        results = self.search_service.search("面试", prompts)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "面试")

    def test_search_empty_keyword(self):
        prompts = [self.p1, self.p2, self.p3]
        results = self.search_service.search("", prompts)
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


def run_tests():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestFileService))
    suite.addTests(loader.loadTestsFromTestCase(TestSearchService))
    suite.addTests(loader.loadTestsFromTestCase(TestMarkdownRenderer))
    suite.addTests(loader.loadTestsFromTestCase(TestClipboardService))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
