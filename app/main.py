import logging
import sys

from PySide6.QtWidgets import QApplication

from app.config import config
from app.ui.main_window import MainWindow


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

    window = MainWindow()
    if not config.start_minimized:
        window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
