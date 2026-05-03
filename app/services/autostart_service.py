import logging
import os
import sys
import winreg

logger = logging.getLogger(__name__)

REGISTRY_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
REGISTRY_VALUE_NAME = "PromptAnywhere"


class AutostartService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _get_startup_command(self) -> str:
        if getattr(sys, "frozen", False):
            return f'"{sys.executable}"'
        pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
        return f'"{pythonw}" "{os.path.abspath(sys.argv[0])}"'

    def set_autostart(self, enabled: bool) -> bool:
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                REGISTRY_KEY_PATH,
                0,
                winreg.KEY_SET_VALUE,
            )
            with key:
                if enabled:
                    command = self._get_startup_command()
                    winreg.SetValueEx(
                        key,
                        REGISTRY_VALUE_NAME,
                        0,
                        winreg.REG_SZ,
                        command,
                    )
                else:
                    try:
                        winreg.DeleteValue(key, REGISTRY_VALUE_NAME)
                    except FileNotFoundError:
                        pass
            return True
        except OSError as e:
            logger.warning("Failed to set autostart (enabled=%s): %s", enabled, e)
            return False

    def is_autostart_enabled(self) -> bool:
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                REGISTRY_KEY_PATH,
                0,
                winreg.KEY_READ,
            )
            with key:
                value, reg_type = winreg.QueryValueEx(key, REGISTRY_VALUE_NAME)
                expected = self._get_startup_command()
                return value == expected
        except FileNotFoundError:
            return False
        except OSError as e:
            logger.warning("Failed to check autostart status: %s", e)
            return False


autostart_service = AutostartService()
