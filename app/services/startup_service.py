import logging
import os
from pathlib import Path

from app.config import config

logger = logging.getLogger(__name__)

DEFAULT_CATEGORIES = ["Coding", "面试", "简历", "日常", "组合模板"]

WELCOME_CONTENT = """# 欢迎使用 Prompt Anywhere

这是一个本地桌面提示词工具。

你可以：
1. 新建提示词
2. 搜索提示词
3. 一键复制
4. 使用模板变量
5. 使用 Composer 组合多个提示词
"""


class StartupService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._is_first_launch = False
        return cls._instance

    def initialize(self):
        self._is_first_launch = not config.data_dir.exists()

        self._ensure_directories()
        self._ensure_config_file()

        if self._is_first_launch or not self._has_user_content():
            self.create_default_categories()
            self.create_welcome_file()

        logger.info("Startup initialization complete. first_launch=%s", self._is_first_launch)

    @property
    def is_first_launch(self) -> bool:
        return self._is_first_launch

    def _ensure_directories(self) -> None:
        backup_dir = Path("./backups").resolve()
        log_dir = Path("./logs").resolve()
        for d in [config.data_dir, config.export_dir, backup_dir, log_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def _ensure_config_file(self) -> None:
        config_path = Path(__file__).parent.parent.parent / "config.yaml"
        if not config_path.exists():
            try:
                import yaml
                default = {
                    "app": {
                        "hotkey": "ctrl+alt+p",
                        "always_on_top": True,
                        "start_minimized": False,
                    },
                    "storage": {
                        "data_dir": "./data",
                        "export_dir": "./exports",
                    },
                }
                config_path.parent.mkdir(parents=True, exist_ok=True)
                with open(config_path, "w", encoding="utf-8") as f:
                    yaml.dump(default, f, allow_unicode=True, sort_keys=False)
                logger.info("Created default config.yaml")
            except Exception as e:
                logger.warning("Failed to create default config.yaml: %s", e)

    def _has_user_content(self) -> bool:
        if not config.data_dir.exists():
            return False
        for item in config.data_dir.rglob("*"):
            if item.is_file() and item.suffix.lower() in config.supported_prompt_extensions:
                return True
        return False

    def check_health(self) -> dict:
        issues = []
        results = {}

        backup_dir = Path("./backups").resolve()
        log_dir = Path("./logs").resolve()

        checks = [
            ("data_dir", config.data_dir),
            ("export_dir", config.export_dir),
            ("backup_dir", backup_dir),
            ("log_dir", log_dir),
        ]

        for name, path in checks:
            writable = self._check_dir_writable(path)
            results[name] = writable
            if not writable:
                issues.append(f"{name} ({path}) is not writable")

        config_path = Path(__file__).parent.parent.parent / "config.yaml"
        config_readable = config_path.exists() and os.access(config_path, os.R_OK)
        results["config_readable"] = config_readable
        if not config_readable:
            issues.append(f"config.yaml ({config_path}) is not readable")

        results["issues"] = issues
        return results

    def _check_dir_writable(self, path: Path) -> bool:
        try:
            path.mkdir(parents=True, exist_ok=True)
            test_file = path / ".write_test"
            test_file.write_text("test", encoding="utf-8")
            test_file.unlink()
            return True
        except Exception:
            return False

    def create_default_categories(self) -> None:
        for category in DEFAULT_CATEGORIES:
            cat_dir = config.data_dir / category
            cat_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Default categories ensured: %s", DEFAULT_CATEGORIES)

    def create_welcome_file(self) -> None:
        welcome_path = config.data_dir / "日常" / "欢迎使用.md"
        if not welcome_path.exists():
            welcome_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                welcome_path.write_text(WELCOME_CONTENT, encoding=config.file_encoding)
                logger.info("Created welcome file: %s", welcome_path)
            except Exception as e:
                logger.warning("Failed to create welcome file: %s", e)


startup_service = StartupService()
