import logging
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.config import config
from app.ui.main_window import MainWindow
from app.ui.quick_window import QuickWindow
from app.ui.tray import TrayManager


def _setup_logging():
    from app.services.logging_service import logging_service
    log_dir = Path("logs")
    logging_service.initialize(log_dir, config.log_level)


def _initialize_app():
    from app.services.startup_service import startup_service
    startup_service.initialize()
    
    from app.services.backup_service import backup_service
    from app.services.config_service import config_service
    
    backup_service.initialize(Path("backups"))
    
    auto_backup_enabled = config_service.get("backup.auto_backup_enabled", True)
    if auto_backup_enabled:
        interval = config_service.get("backup.auto_backup_interval_hours", 24)
        if backup_service.should_auto_backup(interval):
            try:
                backup_service.create_backup(
                    config.data_dir,
                    Path("app_config.json"),
                    config.user_state_path
                )
                logging.getLogger(__name__).info("Auto backup completed")
            except Exception as e:
                logging.getLogger(__name__).warning(f"Auto backup failed: {e}")

    start_with_windows = config_service.get("behavior.start_with_windows", False)
    if start_with_windows:
        from app.services.autostart_service import autostart_service
        if not autostart_service.is_autostart_enabled():
            autostart_service.set_autostart(True)


def _check_existing_data():
    from app.services.startup_service import startup_service
    from PySide6.QtWidgets import QMessageBox
    if startup_service.found_existing_data is not None:
        old = startup_service.found_existing_data
        reply = QMessageBox.question(
            None,
            "发现历史数据",
            f"检测到旧版本数据\n\n位置: {old}\n\n是否自动导入到当前版本？\n（导入后旧数据不受影响）",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if reply == QMessageBox.Yes:
            count = startup_service.import_existing_data()
            if count > 0:
                from app.services.search_service import search_service
                search_service.rebuild_index()
                QMessageBox.information(None, "导入完成", f"已导入 {count} 个提示词文件")


def main():
    _setup_logging()
    _initialize_app()

    app = QApplication(sys.argv)
    app.setApplicationName(config.app_name)
    app.setApplicationVersion(config.app_version)
    app.setQuitOnLastWindowClosed(False)
    from app.utils.icon_utils import create_app_icon
    app.setWindowIcon(create_app_icon())

    _check_existing_data()

    main_window = MainWindow()
    quick_window = QuickWindow()

    def on_open_main(path: str = ""):
        main_window.showNormal()
        main_window.activateWindow()
        main_window.raise_()
        if path:
            from app.services.file_service import PromptFile
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
