import shutil
from pathlib import Path

from app.services.file_service import PromptFile
from app.utils.singleton import Singleton


class ExportService(Singleton):

    def export(self, prompt_file: PromptFile, dest_path: Path) -> bool:
        try:
            shutil.copy2(prompt_file.path, dest_path)
            return True
        except Exception:
            return False


export_service = ExportService()
