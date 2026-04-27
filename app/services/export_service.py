import shutil
from pathlib import Path

from app.services.file_service import PromptFile


class ExportService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def export(self, prompt_file: PromptFile, dest_path: Path) -> bool:
        try:
            shutil.copy2(prompt_file.path, dest_path)
            return True
        except Exception:
            return False


export_service = ExportService()
