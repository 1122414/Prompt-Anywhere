import logging

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QIcon, QPainter, QPen, QPixmap

logger = logging.getLogger(__name__)


def create_app_icon(size: int = 256) -> QIcon:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.TextAntialiasing)

    margin = size // 16
    rect = QRect(margin, margin, size - 2 * margin, size - 2 * margin)
    radius = size // 8

    shadow_rect = QRect(rect.x() + 2, rect.y() + 2, rect.width(), rect.height())
    painter.setPen(Qt.NoPen)
    painter.setBrush(QBrush(QColor(0, 0, 0, 30)))
    painter.drawRoundedRect(shadow_rect, radius, radius)

    painter.setBrush(QBrush(QColor("#1E3A5F")))
    painter.drawRoundedRect(rect, radius, radius)

    inner_rect = QRect(rect.x(), rect.y(), rect.width(), rect.height() - size // 12)
    painter.setBrush(QBrush(QColor("#2563EB")))
    painter.drawRoundedRect(inner_rect, radius, radius)
    painter.setBrush(QBrush(QColor("#2563EB")))
    bottom_rect = QRect(
        rect.x() + radius,
        inner_rect.bottom(),
        rect.width() - 2 * radius,
        size // 12 + 1,
    )
    painter.drawRect(bottom_rect)

    accent_rect = QRect(
        rect.x() + size // 4,
        rect.bottom() - size // 20,
        rect.width() // 2,
        size // 32,
    )
    painter.setBrush(QBrush(QColor("#60A5FA")))
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(accent_rect, size // 64, size // 64)

    text_size = size // 2
    painter.setPen(QPen(QColor("#FFFFFF")))
    font = QFont("Segoe UI", text_size, QFont.Bold)
    painter.setFont(font)
    text_rect = QRect(rect.x(), rect.y(), rect.width(), rect.height() - size // 12)
    painter.drawText(text_rect, Qt.AlignCenter, "PA")

    bracket_size = size // 6
    bracket_y = rect.center().y() + size // 5
    painter.setPen(QPen(QColor("#93C5FD"), max(2, size // 48)))
    font_small = QFont("Segoe UI", bracket_size, QFont.Normal)
    painter.setFont(font_small)
    painter.drawText(
        QRect(rect.x() + size // 6, bracket_y, size // 3, size // 6),
        Qt.AlignCenter,
        "{",
    )
    painter.drawText(
        QRect(rect.right() - size // 3 - size // 6, bracket_y, size // 3, size // 6),
        Qt.AlignCenter,
        "}",
    )

    painter.end()

    icon = QIcon(pixmap)
    for s in (16, 32, 48, 64):
        small = pixmap.scaled(
            s, s, Qt.IgnoreAspectRatio, Qt.SmoothTransformation
        )
        icon.addPixmap(small)

    return icon
