import json
import logging
import re
import sys
from copy import deepcopy
from pathlib import Path


logger = logging.getLogger(__name__)

THEME_PACK_SCHEMA_VERSION = 1
_PACK_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
_HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
_RGBA_COLOR_RE = re.compile(
    r"^rgba\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*"
    r"(0(?:\.\d+)?|1(?:\.0+)?)\s*\)$"
)


def theme_packs_root() -> Path:
    base = (
        Path(sys._MEIPASS)
        if getattr(sys, "frozen", False)
        else Path(__file__).resolve().parents[2]
    )
    return base / "app" / "assets" / "theme_packs"


def theme_pack_manifest_path(pack_id: str) -> Path | None:
    if not _PACK_ID_RE.fullmatch(pack_id):
        return None
    root = theme_packs_root().resolve()
    path = (root / pack_id / "manifest.json").resolve()
    if root not in path.parents:
        return None
    return path


def _safe_palette(value) -> dict:
    if not isinstance(value, dict):
        return {}
    palette = {}
    for key, color in value.items():
        if not isinstance(key, str) or not isinstance(color, str):
            continue
        if _HEX_COLOR_RE.fullmatch(color):
            palette[key] = color
            continue
        match = _RGBA_COLOR_RE.fullmatch(color)
        if match and all(int(channel) <= 255 for channel in match.groups()[:3]):
            palette[key] = color
    return palette


def load_theme_pack(pack_id: str) -> dict:
    manifest_path = theme_pack_manifest_path(pack_id)
    if not manifest_path or not manifest_path.exists():
        return {}
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            value = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        logger.warning(f"Failed to load theme pack {pack_id}: {e}")
        return {}
    if not isinstance(value, dict):
        return {}
    if value.get("schema_version") != THEME_PACK_SCHEMA_VERSION:
        logger.warning(f"Unsupported theme pack schema: {pack_id}")
        return {}
    if value.get("id") != pack_id:
        logger.warning(f"Theme pack id mismatch: {pack_id}")
        return {}

    variants = []
    seen_ids = set()
    pack_root = manifest_path.parent.resolve()
    for item in value.get("variants", []):
        if not isinstance(item, dict):
            continue
        variant_id = str(item.get("id", "")).strip()
        name = str(item.get("name", "")).strip()
        background = str(item.get("background", "")).strip()
        if not variant_id or not name or variant_id in seen_ids:
            continue
        asset_path = (pack_root / background).resolve()
        if (
            pack_root not in asset_path.parents
            or asset_path.suffix.lower() not in _IMAGE_EXTENSIONS
            or not asset_path.exists()
        ):
            logger.warning(f"Invalid theme pack asset: {pack_id}/{variant_id}")
            continue
        seen_ids.add(variant_id)
        variants.append(
            {
                "id": variant_id,
                "name": name,
                "description": str(item.get("description", "")).strip(),
                "background": background,
                "palette": _safe_palette(item.get("palette", {})),
            }
        )
    if not variants:
        return {}

    default_variant = str(value.get("default_variant", "")).strip()
    if default_variant not in seen_ids:
        default_variant = variants[0]["id"]
    return {
        "schema_version": THEME_PACK_SCHEMA_VERSION,
        "id": pack_id,
        "name": str(value.get("name", pack_id)).strip() or pack_id,
        "description": str(value.get("description", "")).strip(),
        "default_variant": default_variant,
        "base_palette": _safe_palette(value.get("base_palette", {})),
        "variants": variants,
        "rights_notice": str(value.get("rights_notice", "")).strip(),
    }


def theme_pack_variants(pack_id: str) -> list[dict]:
    return deepcopy(load_theme_pack(pack_id).get("variants", []))


def theme_pack_variant(pack_id: str, variant_id: str = "") -> dict:
    pack = load_theme_pack(pack_id)
    variants = pack.get("variants", [])
    selected = variant_id or pack.get("default_variant", "")
    for item in variants:
        if item.get("id") == selected:
            return deepcopy(item)
    default_variant = pack.get("default_variant", "")
    for item in variants:
        if item.get("id") == default_variant:
            return deepcopy(item)
    return deepcopy(variants[0]) if variants else {}


def theme_pack_asset(pack_id: str, variant_id: str = "") -> Path | None:
    manifest_path = theme_pack_manifest_path(pack_id)
    variant = theme_pack_variant(pack_id, variant_id)
    background = str(variant.get("background", ""))
    if not manifest_path or not background:
        return None
    pack_root = manifest_path.parent.resolve()
    path = (pack_root / background).resolve()
    if pack_root not in path.parents:
        return None
    return path if path.exists() else None
