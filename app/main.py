import logging
import sys

from PySide6.QtWidgets import QApplication

from app.config import config
from app.ui.main_window import MainWindow
from app.ui.quick_window import QuickWindow
from app.ui.tray import TrayManager


def _setup_logging():
    level = getattr(logging, config.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main():
    _setup_logging()
    app = QApplication(sys.argv)
    app.setApplicationName(config.app_name)
    app.setApplicationVersion(config.app_version)
    app.setQuitOnLastWindowClosed(False)

    main_window = MainWindow()
    quick_window = QuickWindow()

    def on_open_main(path: str = ""):
        main_window.showNormal()
        main_window.activateWindow()
        main_window.raise_()
        if path:
            from app.services.file_service import PromptFile
            from pathlib import Path
            full_path = config.data_dir / path
            if full_path.exists():
                main_window._on_prompt_selected(PromptFile(full_path))

    quick_window.open_main_requested.connect(on_open_main)

    main_window.quick_window = quick_window
    quick_window.main_window = main_window

    if not config.start_minimized:
        main_window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
