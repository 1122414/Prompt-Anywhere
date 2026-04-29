import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import Config
from app.services.config_service import ConfigService
from app.services.backup_service import BackupService
from app.services.history_service import HistoryService
from app.services.startup_service import StartupService
from app.services.diagnostics_service import DiagnosticsService


class TestConfigService(unittest.TestCase):
    def setUp(self):
        Config._instance = None
        ConfigService._instance = None
        self.test_dir = Path(tempfile.mkdtemp())
        self.config_path = self.test_dir / "app_config.json"
        os.environ["APP_CONFIG_PATH"] = str(self.config_path)
        self.service = ConfigService()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
        Config._instance = None
        ConfigService._instance = None

    def test_get_default(self):
        self.assertEqual(self.service.get("storage.data_dir"), "./data")

    def test_set_and_get(self):
        self.service.set("storage.data_dir", "/custom/path")
        self.assertEqual(self.service.get("storage.data_dir"), "/custom/path")

    def test_nested_key(self):
        self.service.set("window.opacity", 0.8)
        self.assertEqual(self.service.get("window.opacity"), 0.8)


class TestBackupService(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.data_dir = self.test_dir / "data"
        self.data_dir.mkdir()
        self.backup_dir = self.test_dir / "backups"
        self.backup_dir.mkdir()
        
        (self.data_dir / "test.md").write_text("test content")
        
        BackupService._instance = None
        self.service = BackupService()
        self.service.initialize(self.backup_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
        BackupService._instance = None

    def test_create_backup(self):
        config_path = self.test_dir / "app_config.json"
        config_path.write_text("{}")
        state_path = self.test_dir / "app_state.json"
        state_path.write_text("{}")
        
        backup_path = self.service.create_backup(self.data_dir, config_path, state_path)
        self.assertTrue(backup_path.exists())
        self.assertTrue(backup_path.name.startswith("backup_"))

    def test_list_backups(self):
        config_path = self.test_dir / "app_config.json"
        config_path.write_text("{}")
        state_path = self.test_dir / "app_state.json"
        state_path.write_text("{}")
        
        self.service.create_backup(self.data_dir, config_path, state_path)
        backups = self.service.list_backups()
        self.assertEqual(len(backups), 1)


class TestHistoryService(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.file_path = self.test_dir / "test.md"
        self.file_path.write_text("original content")
        
        HistoryService._instance = None
        self.service = HistoryService()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
        HistoryService._instance = None

    def test_create_version(self):
        result = self.service.create_version(self.file_path, "new content")
        self.assertTrue(result)

    def test_list_versions(self):
        self.service.create_version(self.file_path, "version 1")
        self.file_path.write_text("version 1")
        self.service.create_version(self.file_path, "version 2")
        versions = self.service.list_versions(self.file_path)
        self.assertEqual(len(versions), 2)


class TestStartupService(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        os.environ["DATA_DIR"] = str(self.test_dir / "data")
        os.environ["EXPORT_DIR"] = str(self.test_dir / "exports")
        
        Config._instance = None
        StartupService._instance = None
        self.service = StartupService()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
        Config._instance = None
        StartupService._instance = None

    def test_initialize(self):
        self.service.initialize()
        self.assertTrue((self.test_dir / "data").exists())
        self.assertTrue((self.test_dir / "exports").exists())

    def test_health_check(self):
        health = self.service.check_health()
        self.assertIn("data_dir", health)
        self.assertIn("issues", health)


class TestDiagnosticsService(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        DiagnosticsService._instance = None
        self.service = DiagnosticsService()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
        DiagnosticsService._instance = None

    def test_export_diagnostics(self):
        output_path = self.test_dir / "diagnostics.zip"
        result = self.service.export_diagnostics(output_path)
        self.assertTrue(result)
        self.assertTrue(output_path.exists())


def run_tests():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestConfigService))
    suite.addTests(loader.loadTestsFromTestCase(TestBackupService))
    suite.addTests(loader.loadTestsFromTestCase(TestHistoryService))
    suite.addTests(loader.loadTestsFromTestCase(TestStartupService))
    suite.addTests(loader.loadTestsFromTestCase(TestDiagnosticsService))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
