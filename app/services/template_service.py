import logging
import re
from re import Match

from app.config import config

logger = logging.getLogger(__name__)

_VALID_NAME_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


class TemplateService:
    _instance: "TemplateService | None" = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def extract_variables(self, content: str) -> list[str]:
        if not content:
            return []
        pattern = re.compile(config.template_variable_pattern)
        matches = pattern.findall(content)
        unique = sorted(set(matches))
        max_count = config.template_variable_max_count
        if len(unique) > max_count:
            logger.warning(f"Found {len(unique)} unique variables, truncating to max {max_count}")
            unique = unique[:max_count]
        return unique

    def validate_variable_name(self, name: str) -> tuple[bool, str]:
        if not name:
            return False, "变量名不能为空"
        if not _VALID_NAME_RE.match(name):
            return False, f"无效的变量名: '{name}'，仅允许字母、数字和下划线，且不能以数字开头"
        if len(name) > 100:
            return False, "变量名过长，最大长度为100个字符"
        return True, ""

    def make_variable_token(self, name: str) -> str:
        return f"{{{{{name}}}}}"

    def render(self, content: str, values: dict[str, str]) -> str:
        if not content or not values:
            return content
        pattern = re.compile(config.template_variable_pattern)

        def _replace(match: Match[str]) -> str:
            var_name = match.group(1) or ""
            return values.get(var_name, match.group(0) or "")

        return pattern.sub(_replace, content)

    def replace_selection(
        self, content: str, start: int, end: int, variable_name: str
    ) -> str:
        if not content:
            return self.make_variable_token(variable_name)
        if start < 0:
            start = 0
        if end > len(content):
            end = len(content)
        if start > end:
            start = end
        token = self.make_variable_token(variable_name)
        return content[:start] + token + content[end:]


template_service = TemplateService()
