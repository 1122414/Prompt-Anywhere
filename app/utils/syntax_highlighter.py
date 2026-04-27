from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat


class MarkdownHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_formats()
        self._setup_rules()

    def _setup_formats(self):
        self.header_format = QTextCharFormat()
        self.header_format.setFontWeight(QFont.Bold)
        self.header_format.setForeground(QColor("#005cc5"))

        self.bold_format = QTextCharFormat()
        self.bold_format.setFontWeight(QFont.Bold)

        self.italic_format = QTextCharFormat()
        self.italic_format.setFontItalic(True)

        self.code_format = QTextCharFormat()
        self.code_format.setFontFamily("Consolas, monospace")
        self.code_format.setForeground(QColor("#e36209"))
        self.code_format.setBackground(QColor("#f6f8fa"))

        self.link_format = QTextCharFormat()
        self.link_format.setForeground(QColor("#0366d6"))
        self.link_format.setUnderlineStyle(QTextCharFormat.SingleUnderline)

        self.list_format = QTextCharFormat()
        self.list_format.setForeground(QColor("#22863a"))

        self.quote_format = QTextCharFormat()
        self.quote_format.setForeground(QColor("#6a737d"))
        self.quote_format.setFontItalic(True)

        self.strikethrough_format = QTextCharFormat()
        self.strikethrough_format.setForeground(QColor("#6a737d"))

    def _setup_rules(self):
        self.rules = [
            (QRegularExpression(r"^#{1,6}\s.*"), self.header_format),
            (QRegularExpression(r"\*\*[^*]+\*\*"), self.bold_format),
            (QRegularExpression(r"__[^_]+__"), self.bold_format),
            (QRegularExpression(r"(?<![*])\*[^*]+\*(?![*])"), self.italic_format),
            (QRegularExpression(r"(?<!_)_[^_]+_(?!_)"), self.italic_format),
            (QRegularExpression(r"`[^`]+`"), self.code_format),
            (QRegularExpression(r"\[([^\]]+)\]\(([^)]+)\)"), self.link_format),
            (QRegularExpression(r"^\s*[-*+]\s"), self.list_format),
            (QRegularExpression(r"^\s*\d+\.\s"), self.list_format),
            (QRegularExpression(r"^\s*\>\s.*"), self.quote_format),
            (QRegularExpression(r"~~[^~]+~~"), self.strikethrough_format),
        ]

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)

        self._highlight_code_blocks(text)

    def _highlight_code_blocks(self, text):
        if text.strip().startswith("```"):
            self.setFormat(0, len(text), self.code_format)
