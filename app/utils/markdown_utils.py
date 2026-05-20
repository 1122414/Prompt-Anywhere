import markdown
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound

from app.config import config
from app.ui.theme import markdown_stylesheet


class MarkdownRenderer:
    _instance = None
    _md = None
    _formatter = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_renderer()
        return cls._instance

    def _init_renderer(self):
        self._md = markdown.Markdown(
            extensions=[
                "tables",
                "fenced_code",
                "nl2br",
                "toc",
            ]
        )
        self._formatter = HtmlFormatter(
            style=config.pygments_style,
            cssclass="codehilite",
            wrapcode=True,
        )

    def _highlight_code(self, text):
        def replace_code_block(match):
            code = match.group(2)
            lang = match.group(1) or ""
            try:
                if lang:
                    lexer = get_lexer_by_name(lang)
                else:
                    lexer = guess_lexer(code)
            except ClassNotFound:
                lexer = get_lexer_by_name("text")
            highlighted = highlight(code, lexer, self._formatter)
            return highlighted

        import re
        pattern = r'<pre><code class="language-([^"]*)">(.*?)</code></pre>'
        return re.sub(pattern, replace_code_block, text, flags=re.DOTALL)

    def render(self, text):
        self._md.reset()
        html = self._md.convert(text)
        html = self._highlight_code(html)
        css = self._formatter.get_style_defs(".codehilite")
        return f"""
        {markdown_stylesheet(css)}
        <body>{html}</body>
        """


renderer = MarkdownRenderer()
