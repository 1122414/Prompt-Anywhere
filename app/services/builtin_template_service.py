import logging
from pathlib import Path
from typing import Dict, List, Tuple

from app.config import config
from app.services.file_service import file_service

logger = logging.getLogger(__name__)


class BuiltinTemplateService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._template_dir = config.builtin_template_dir
        return cls._instance

    def list_templates(self) -> List[Dict[str, str]]:
        if not config.enable_builtin_templates:
            return []

        template_dir = self._template_dir
        if not template_dir.exists():
            logger.warning(f"Builtin template directory not found: {template_dir}")
            return []

        templates = []
        for path in sorted(template_dir.rglob("*.md")):
            if path.is_file():
                rel_path = path.relative_to(template_dir)
                category = rel_path.parent.name if rel_path.parent != Path(".") else ""
                templates.append({
                    "name": path.stem,
                    "path": rel_path.as_posix(),
                    "category": category,
                })

        templates.sort(key=lambda t: (t["category"], t["name"]))
        return templates

    def import_templates(self, template_paths: List[str], target_category: str) -> Tuple[int, List[str]]:
        success_count = 0
        error_messages = []

        for template_path in template_paths:
            try:
                src_path = self._template_dir / template_path
                if not src_path.exists():
                    error_messages.append(f"模板不存在: {template_path}")
                    continue

                content = src_path.read_text(encoding=config.file_encoding)
                name = Path(template_path).stem
                result = file_service.create_prompt(
                    parent_path=target_category,
                    name=name,
                    extension=".md",
                    content=content,
                )
                if result is not None:
                    success_count += 1
                    logger.info(f"Imported template '{name}' to '{target_category}'")
                else:
                    error_messages.append(f"导入失败（可能已存在）: {template_path}")
            except Exception as e:
                logger.warning(f"Failed to import template '{template_path}': {e}")
                error_messages.append(f"导入出错: {template_path} - {e}")

        return success_count, error_messages

    def get_template_content(self, template_path: str) -> str:
        try:
            src_path = self._template_dir / template_path
            if not src_path.exists():
                logger.warning(f"Template file not found: {src_path}")
                return ""
            return src_path.read_text(encoding=config.file_encoding)
        except Exception as e:
            logger.warning(f"Failed to read template '{template_path}': {e}")
            return ""


builtin_template_service = BuiltinTemplateService()
