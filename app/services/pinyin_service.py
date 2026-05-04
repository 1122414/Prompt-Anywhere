import logging
from typing import Dict

from pypinyin import Style, lazy_pinyin

from app.utils.singleton import Singleton

logger = logging.getLogger(__name__)


class PinyinService(Singleton):

    def _init(self):
        self._cache: Dict[str, Dict[str, str]] = {}

    def get_full_pinyin(self, text: str) -> str:
        if not text:
            return ""
        try:
            pinyin_list = lazy_pinyin(text, style=Style.NORMAL)
            return "".join(pinyin_list)
        except Exception as e:
            logger.warning(f"Failed to convert to pinyin: {e}")
            return ""

    def get_initials(self, text: str) -> str:
        if not text:
            return ""
        try:
            pinyin_list = lazy_pinyin(text, style=Style.FIRST_LETTER)
            return "".join(pinyin_list)
        except Exception as e:
            logger.warning(f"Failed to convert to initials: {e}")
            return ""

    def build_pinyin_fields(self, text: str) -> Dict[str, str]:
        if not text:
            return {"full": "", "initials": "", "tokens": []}

        cache_key = text
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            pinyin_list = lazy_pinyin(text, style=Style.NORMAL)
            full_pinyin = "".join(pinyin_list)
            tokens = [p for p in pinyin_list if p]

            initials_list = lazy_pinyin(text, style=Style.FIRST_LETTER)
            initials = "".join(initials_list)

            result = {
                "full": full_pinyin,
                "initials": initials,
                "tokens": tokens,
            }
            self._cache[cache_key] = result
            return result
        except Exception as e:
            logger.warning(f"Failed to build pinyin fields: {e}")
            return {"full": "", "initials": "", "tokens": []}


pinyin_service = PinyinService()
