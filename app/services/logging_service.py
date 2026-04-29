import logging
import os
import platform
import sys
import threading
import traceback
from logging.handlers import RotatingFileHandler
from pathlib import Path


_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class LoggingService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def initialize(self, log_dir: Path, level: str = "INFO", max_bytes_mb: int = 10, backup_count: int = 5):
        if self._initialized:
            return
        self._initialized = True

        self._log_dir = Path(log_dir)
        self._log_dir.mkdir(parents=True, exist_ok=True)

        self._log_level = getattr(logging, level.upper(), logging.INFO)
        self._max_bytes = max_bytes_mb * 1024 * 1024
        self._backup_count = backup_count

        formatter = logging.Formatter(_LOG_FORMAT, datefmt=_LOG_DATE_FORMAT)

        app_log_path = self._log_dir / "app.log"
        self._app_handler = RotatingFileHandler(
            app_log_path,
            maxBytes=self._max_bytes,
            backupCount=self._backup_count,
            encoding="utf-8",
        )
        self._app_handler.setLevel(self._log_level)
        self._app_handler.setFormatter(formatter)

        error_log_path = self._log_dir / "error.log"
        self._error_handler = RotatingFileHandler(
            error_log_path,
            maxBytes=self._max_bytes,
            backupCount=self._backup_count,
            encoding="utf-8",
        )
        self._error_handler.setLevel(logging.WARNING)
        self._error_handler.setFormatter(formatter)

        self._console_handler = logging.StreamHandler(sys.stdout)
        self._console_handler.setLevel(self._log_level)
        self._console_handler.setFormatter(formatter)

        root = logging.getLogger()
        root.setLevel(self._log_level)
        root.addHandler(self._app_handler)
        root.addHandler(self._error_handler)
        root.addHandler(self._console_handler)

        self._original_excepthook = sys.excepthook
        sys.excepthook = self._handle_uncaught_exception
        threading.excepthook = self._handle_thread_exception

    def get_logger(self, name: str) -> logging.Logger:
        return logging.getLogger(name)

    def log_exception(self, e: Exception, context: str = ""):
        logger = logging.getLogger("app.exception")
        tb = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        if context:
            logger.error(f"[{context}] {type(e).__name__}: {e}\n{tb}")
        else:
            logger.error(f"{type(e).__name__}: {e}\n{tb}")

    def export_diagnostics(self, output_path: Path):
        import datetime

        lines = []
        lines.append("=" * 60)
        lines.append("Prompt Anywhere - Diagnostic Report")
        lines.append(f"Generated: {datetime.datetime.now().isoformat()}")
        lines.append("=" * 60)

        lines.append("")
        lines.append("[System Info]")
        lines.append(f"  Platform: {platform.platform()}")
        lines.append(f"  Python: {sys.version}")
        lines.append(f"  Architecture: {platform.architecture()[0]}")
        lines.append(f"  Machine: {platform.machine()}")

        try:
            from app.config import config
            lines.append("")
            lines.append("[App Info]")
            lines.append(f"  Name: {config.app_name}")
            lines.append(f"  Version: {config.app_version}")
            lines.append(f"  Env: {config.app_env}")
            lines.append(f"  Log Level: {config.log_level}")
            lines.append(f"  Data Dir: {config.data_dir}")
            lines.append(f"  Hotkey: {config.hotkey}")
        except Exception as e:
            lines.append(f"  [Error reading config: {e}]")

        app_log = self._log_dir / "app.log"
        lines.append("")
        lines.append("[Recent App Log (last 200 lines)]")
        if app_log.exists():
            try:
                all_lines = app_log.read_text(encoding="utf-8").splitlines()
                for line in all_lines[-200:]:
                    lines.append(f"  {line}")
            except Exception as e:
                lines.append(f"  [Error reading log: {e}]")
        else:
            lines.append("  (no app.log found)")

        error_log = self._log_dir / "error.log"
        lines.append("")
        lines.append("[Recent Error Log (last 100 lines)]")
        if error_log.exists():
            try:
                all_lines = error_log.read_text(encoding="utf-8").splitlines()
                for line in all_lines[-100:]:
                    lines.append(f"  {line}")
            except Exception as e:
                lines.append(f"  [Error reading log: {e}]")
        else:
            lines.append("  (no error.log found)")

        lines.append("")
        lines.append("[Environment Variables (filtered)]")
        sensitive_keys = {"MODEL_API_KEY", "API_KEY", "SECRET", "TOKEN", "PASSWORD"}
        for key in sorted(os.environ):
            if any(s in key.upper() for s in sensitive_keys):
                continue
            if key.startswith(("APP_", "LOG_", "DATA_", "UI_", "SEARCH_", "COPY_", "ESC_", "COMPOSER_", "TEMPLATE_", "ENABLE_", "SHOW_", "DEFAULT_", "PYGMENTS_", "GLOBAL_", "QUICK_", "SUPPORTED_", "IMAGE_", "PASTED_", "MAX_", "MIN_", "ALWAYS_", "START_", "BUILTIN_", "FILE_")):
                lines.append(f"  {key}={os.environ[key]}")

        lines.append("")
        lines.append("=" * 60)
        lines.append("End of Diagnostic Report")
        lines.append("=" * 60)

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(lines), encoding="utf-8")

    def _handle_uncaught_exception(self, exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            self._original_excepthook(exc_type, exc_value, exc_tb)
            return
        logger = logging.getLogger("app.exception")
        tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        logger.critical(f"Uncaught exception:\n{tb}")

    def _handle_thread_exception(self, args):
        logger = logging.getLogger("app.exception")
        tb = "".join(traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback))
        logger.critical(f"Unhandled thread exception:\n{tb}")


logging_service = LoggingService()
