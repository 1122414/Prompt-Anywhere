import markdown
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound

from app.config import config


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
        <style>
            body {{ font-family: system-ui, -apple-system, sans-serif; line-height: 1.6; padding: 16px; }}
            h1, h2, h3, h4, h5, h6 {{ margin-top: 24px; margin-bottom: 16px; font-weight: 600; }}
            h1 {{ font-size: 2em; border-bottom: 1px solid #e1e4e8; padding-bottom: 0.3em; }}
            h2 {{ font-size: 1.5em; border-bottom: 1px solid #e1e4e8; padding-bottom: 0.3em; }}
            code {{ background-color: rgba(175, 184, 193, 0.2); padding: 0.2em 0.4em; border-radius: 6px; font-size: 85%; }}
            pre {{ background-color: #f6f8fa; padding: 16px; overflow: auto; border-radius: 6px; }}
            pre code {{ background-color: transparent; padding: 0; }}
            blockquote {{ padding: 0 1em; color: #656d76; border-left: 0.25em solid #d0d7de; margin: 0; }}
            table {{ border-collapse: collapse; width: 100%; margin: 16px 0; }}
            th, td {{ border: 1px solid #d0d7de; padding: 6px 13px; }}
            th {{ background-color: #f6f8fa; }}
            ul, ol {{ padding-left: 2em; }}
            li + li {{ margin-top: 0.25em; }}
            hr {{ height: 0.25em; padding: 0; margin: 24px 0; background-color: #d0d7de; border: 0; }}
            {css}
        </style>
        <body>{html}</body>
        """


renderer = MarkdownRenderer()
