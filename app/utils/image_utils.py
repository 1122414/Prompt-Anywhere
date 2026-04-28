import logging
import shutil
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QMimeData
from PySide6.QtGui import QImage

from app.config import config

logger = logging.getLogger(__name__)


def save_pasted_image(mime_data: QMimeData, prompt_path: Path) -> str | None:
    if mime_data.hasImage():
        image = mime_data.imageData()
        if isinstance(image, QImage):
            return _save_image(image, prompt_path)

    urls = mime_data.urls()
    if urls:
        for url in urls:
            if url.isLocalFile():
                src_path = Path(url.toLocalFile())
                if src_path.suffix.lower() in (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"):
                    return _copy_image_file(src_path, prompt_path)

    return None


def _save_image(image: QImage, prompt_path: Path) -> str | None:
    assets_dir = _ensure_assets_dir(prompt_path)
    if not assets_dir:
        return None

    sub_dir = assets_dir / prompt_path.stem
    sub_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}.{config.pasted_image_format}"
    filepath = sub_dir / filename

    fmt = config.pasted_image_format.upper()
    if fmt == "JPG":
        fmt = "JPEG"

    if image.save(str(filepath), fmt):
        rel = filepath.relative_to(prompt_path.parent).as_posix()
        return rel
    return None


def _copy_image_file(src_path: Path, prompt_path: Path) -> str | None:
    assets_dir = _ensure_assets_dir(prompt_path)
    if not assets_dir:
        return None

    sub_dir = assets_dir / prompt_path.stem
    sub_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ext = src_path.suffix.lower()
    if ext == ".jpeg":
        ext = ".jpg"
    filename = f"{timestamp}{ext}"
    filepath = sub_dir / filename

    try:
        shutil.copy2(str(src_path), str(filepath))
        rel = filepath.relative_to(prompt_path.parent).as_posix()
        return rel
    except Exception as e:
        logger.warning(f"Failed to copy image: {e}")
        return None


def _ensure_assets_dir(prompt_path: Path) -> Path | None:
    try:
        parent_dir = prompt_path.parent
        assets_dir = parent_dir / config.image_assets_dir_name
        assets_dir.mkdir(parents=True, exist_ok=True)
        return assets_dir
    except Exception as e:
        logger.warning(f"Failed to create assets dir: {e}")
        return None
