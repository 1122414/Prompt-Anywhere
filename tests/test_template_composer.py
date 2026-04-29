import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import Config
from app.services.template_service import TemplateService
from app.services.composer_service import ComposerService
from app.services.builtin_template_service import BuiltinTemplateService
from app.services.file_service import FileService, PromptFile


class TestTemplateService(unittest.TestCase):
    def setUp(self):
        Config._instance = None
        TemplateService._instance = None
        self.service = TemplateService()

    def tearDown(self):
        Config._instance = None
        TemplateService._instance = None

    def test_extract_variables(self):
        content = "Hello {{name}}, your project is {{project}}"
        variables = self.service.extract_variables(content)
        self.assertEqual(variables, ["name", "project"])

    def test_extract_variables_dedup(self):
        content = "{{a}} and {{a}} and {{b}}"
        variables = self.service.extract_variables(content)
        self.assertEqual(variables, ["a", "b"])

    def test_extract_variables_empty(self):
        self.assertEqual(self.service.extract_variables(""), [])
        self.assertEqual(self.service.extract_variables(None), [])

    def test_validate_variable_name_valid(self):
        is_valid, _ = self.service.validate_variable_name("project_name")
        self.assertTrue(is_valid)
        is_valid, _ = self.service.validate_variable_name("_private")
        self.assertTrue(is_valid)
        is_valid, _ = self.service.validate_variable_name("camelCase")
        self.assertTrue(is_valid)

    def test_validate_variable_name_invalid(self):
        is_valid, _ = self.service.validate_variable_name("")
        self.assertFalse(is_valid)
        is_valid, _ = self.service.validate_variable_name("123bad")
        self.assertFalse(is_valid)
        is_valid, _ = self.service.validate_variable_name("project-name")
        self.assertFalse(is_valid)
        is_valid, _ = self.service.validate_variable_name("项目名称")
        self.assertFalse(is_valid)

    def test_make_variable_token(self):
        self.assertEqual(self.service.make_variable_token("name"), "{{name}}")
        self.assertEqual(self.service.make_variable_token("project_name"), "{{project_name}}")

    def test_render(self):
        content = "Hello {{name}}, welcome to {{project}}!"
        values = {"name": "World", "project": "Prompt Anywhere"}
        result = self.service.render(content, values)
        self.assertEqual(result, "Hello World, welcome to Prompt Anywhere!")

    def test_render_missing_var(self):
        content = "Hello {{name}}, your project is {{project}}"
        values = {"name": "World"}
        result = self.service.render(content, values)
        self.assertEqual(result, "Hello World, your project is {{project}}")

    def test_render_empty(self):
        self.assertEqual(self.service.render("", {"a": "b"}), "")
        self.assertEqual(self.service.render("hello", {}), "hello")

    def test_replace_selection(self):
        content = "Hello World"
        result = self.service.replace_selection(content, 6, 11, "target")
        self.assertEqual(result, "Hello {{target}}")


class TestComposerService(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.data_dir = self.test_dir / "data"
        self.data_dir.mkdir()

        os.environ["DATA_DIR"] = str(self.data_dir)
        Config._instance = None
        FileService._instance = None
        ComposerService._instance = None

        self.config = Config()
        self.file_service = FileService()
        self.composer_service = ComposerService()

        self.file_service.create_category("Test")
        self.file_service.create_prompt("Test", "file1", ".md", "Content of file1")
        self.file_service.create_prompt("Test", "file2", ".md", "Content of file2")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
        if "DATA_DIR" in os.environ:
            del os.environ["DATA_DIR"]
        Config._instance = None
        FileService._instance = None
        ComposerService._instance = None

    def test_initial_state(self):
        self.assertEqual(self.composer_service.get_files(), [])

    def test_add_file(self):
        result = self.composer_service.add_file("Test/file1.md")
        self.assertTrue(result)
        self.assertEqual(self.composer_service.get_files(), ["Test/file1.md"])

    def test_add_file_duplicate(self):
        self.composer_service.add_file("Test/file1.md")
        result = self.composer_service.add_file("Test/file1.md")
        self.assertFalse(result)
        self.assertEqual(len(self.composer_service.get_files()), 1)

    def test_remove_file(self):
        self.composer_service.add_file("Test/file1.md")
        result = self.composer_service.remove_file("Test/file1.md")
        self.assertTrue(result)
        self.assertEqual(self.composer_service.get_files(), [])

    def test_remove_file_not_found(self):
        result = self.composer_service.remove_file("nonexistent.md")
        self.assertFalse(result)

    def test_move_up_down(self):
        self.composer_service.add_file("Test/file1.md")
        self.composer_service.add_file("Test/file2.md")

        self.assertTrue(self.composer_service.move_up(1))
        self.assertEqual(self.composer_service.get_files(), ["Test/file2.md", "Test/file1.md"])

        self.assertTrue(self.composer_service.move_down(0))
        self.assertEqual(self.composer_service.get_files(), ["Test/file1.md", "Test/file2.md"])

    def test_move_boundary(self):
        self.composer_service.add_file("Test/file1.md")
        self.assertFalse(self.composer_service.move_up(0))
        self.assertFalse(self.composer_service.move_down(0))

    def test_clear(self):
        self.composer_service.add_file("Test/file1.md")
        self.composer_service.add_file("Test/file2.md")
        self.composer_service.clear()
        self.assertEqual(self.composer_service.get_files(), [])

    def test_build(self):
        self.composer_service.add_file("Test/file1.md")
        self.composer_service.add_file("Test/file2.md")
        result = self.composer_service.build()
        self.assertIn("Content of file1", result)
        self.assertIn("Content of file2", result)
        self.assertIn("# file1", result)
        self.assertIn("# file2", result)

    def test_build_empty(self):
        self.assertEqual(self.composer_service.build(), "")


class TestBuiltinTemplateService(unittest.TestCase):
    def setUp(self):
        Config._instance = None
        BuiltinTemplateService._instance = None
        self.service = BuiltinTemplateService()

    def tearDown(self):
        Config._instance = None
        BuiltinTemplateService._instance = None

    def test_list_templates(self):
        templates = self.service.list_templates()
        self.assertIsInstance(templates, list)
        self.assertEqual(len(templates), 6)

    def test_template_structure(self):
        templates = self.service.list_templates()
        if templates:
            template = templates[0]
            self.assertIn("name", template)
            self.assertIn("path", template)
            self.assertIn("category", template)

    def test_get_template_content(self):
        templates = self.service.list_templates()
        if templates:
            content = self.service.get_template_content(templates[0]["path"])
            self.assertIsInstance(content, str)
            self.assertTrue(len(content) > 0)


def run_tests():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestTemplateService))
    suite.addTests(loader.loadTestsFromTestCase(TestComposerService))
    suite.addTests(loader.loadTestsFromTestCase(TestBuiltinTemplateService))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
