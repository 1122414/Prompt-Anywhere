import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional

from app.config import config
from app.providers.llm.base import LLMProvider
from app.providers.llm.openai_compatible import OllamaProvider, OpenAICompatibleProvider

logger = logging.getLogger(__name__)


@dataclass
class TemplateVariable:
    name: str
    var_type: str = "text"
    default: str = ""
    description: str = ""


class AITemplateService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._provider: Optional[LLMProvider] = None
        return cls._instance

    def _get_provider(self) -> Optional[LLMProvider]:
        if not config.ai_template_enabled:
            return None
        if self._provider is not None:
            return self._provider

        provider_name = config.ai_template_provider
        if provider_name == "ollama":
            self._provider = OllamaProvider()
        else:
            self._provider = OpenAICompatibleProvider()

        if not self._provider.is_configured():
            return None
        return self._provider

    def detect_variables_rule(self, content: str) -> List[TemplateVariable]:
        variables = []
        seen_values = set()
        used_names = set()

        rules = [
            (r"https?://[^\s\"'\)]+", "链接"),
            (r"[\w.-]+@[\w.-]+\.\w+", "邮箱"),
            (r"\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?", "日期"),
            (r"\d+\s*[个件条页篇份套种张次]+", "数量"),
            (r'["\']([^"\']{3,50})["\']', "主题"),
            (r"小红书|抖音|B站|微信公众号|微博|知乎", "平台"),
            (r"产品经理|程序员|设计师|运营|分析师|工程师", "角色"),
        ]

        for pattern, default_name in rules:
            for match in re.finditer(pattern, content):
                value = match.group(1) if match.lastindex else match.group(0)
                if value and value not in seen_values:
                    seen_values.add(value)
                    var_name = self._generate_var_name(default_name, used_names)
                    used_names.add(var_name)
                    variables.append(TemplateVariable(
                        name=var_name,
                        var_type=self._infer_type(pattern, value),
                        default=value,
                        description=f"自动识别: {default_name}",
                    ))

        return variables[:10]

    def detect_variables_ai(self, content: str) -> List[TemplateVariable]:
        provider = self._get_provider()
        if not provider:
            return []

        prompt = (
            "分析以下提示词，找出适合抽象成模板变量的片段。"
            "返回JSON数组，每个元素包含: name(变量名), type(text/multiline/url/number/select), default(默认值)。\n\n"
            f"提示词内容:\n{content}\n\n"
            "要求:\n"
            "1. 变量名使用中文，简洁明了\n"
            "2. 只识别真正可变的部分\n"
            "3. 返回严格JSON格式，不要Markdown代码块"
        )

        messages = [{"role": "user", "content": prompt}]
        result = provider.chat_json(
            messages,
            temperature=config.ai_template_temperature,
            timeout=config.ai_template_timeout_seconds,
        )

        if not result or not isinstance(result, list):
            return []

        variables = []
        for item in result:
            if isinstance(item, dict) and "name" in item:
                variables.append(TemplateVariable(
                    name=item["name"],
                    var_type=item.get("type", "text"),
                    default=str(item.get("default", "")),
                    description=item.get("description", ""),
                ))
        return variables

    def detect_variables(self, content: str) -> List[TemplateVariable]:
        mode = config.ai_template_detection_mode
        rule_vars = self.detect_variables_rule(content)

        if mode == "rule":
            return rule_vars

        if mode == "ai":
            return self.detect_variables_ai(content) or rule_vars

        # hybrid mode
        ai_vars = self.detect_variables_ai(content)
        if ai_vars:
            return ai_vars
        return rule_vars

    def apply_variables(self, content: str, variables: List[TemplateVariable]) -> str:
        result = content
        for var in variables:
            if var.default and var.default in result:
                token = f"{{{{{var.name}}}}}"
                result = result.replace(var.default, token, 1)
        return result

    def _generate_var_name(self, base: str, used_names: set) -> str:
        if base not in used_names:
            return base
        for i in range(2, 20):
            name = f"{base}{i}"
            if name not in used_names:
                return name
        return base

    def _infer_type(self, pattern: str, value: str) -> str:
        if "http" in pattern:
            return "url"
        if "@" in value and "." in value:
            return "email"
        if re.match(r"^\d+$", value):
            return "number"
        if len(value) > 30:
            return "multiline"
        return "text"


ai_template_service = AITemplateService()
