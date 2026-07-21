import math

from PySide6.QtCore import QPointF, QRect, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QIcon,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QPolygonF,
)


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


def create_theme_icon(kind: str, color: str, size: int = 18) -> QIcon:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    stroke = QColor(color)
    fill = QColor(stroke)
    fill.setAlpha(34)
    pen = QPen(stroke, max(1.4, size / 11))
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)

    if kind == "folder":
        path = QPainterPath()
        path.moveTo(size * 0.12, size * 0.34)
        path.lineTo(size * 0.12, size * 0.24)
        path.quadTo(size * 0.12, size * 0.17, size * 0.2, size * 0.17)
        path.lineTo(size * 0.43, size * 0.17)
        path.lineTo(size * 0.54, size * 0.31)
        path.lineTo(size * 0.82, size * 0.31)
        path.quadTo(size * 0.89, size * 0.31, size * 0.89, size * 0.39)
        path.lineTo(size * 0.89, size * 0.77)
        path.quadTo(size * 0.89, size * 0.84, size * 0.81, size * 0.84)
        path.lineTo(size * 0.2, size * 0.84)
        path.quadTo(size * 0.12, size * 0.84, size * 0.12, size * 0.76)
        path.closeSubpath()
        painter.setBrush(fill)
        painter.drawPath(path)
    elif kind == "file":
        body = QPainterPath()
        body.moveTo(size * 0.27, size * 0.11)
        body.lineTo(size * 0.59, size * 0.11)
        body.lineTo(size * 0.78, size * 0.3)
        body.lineTo(size * 0.78, size * 0.84)
        body.lineTo(size * 0.27, size * 0.84)
        body.closeSubpath()
        painter.setBrush(fill)
        painter.drawPath(body)
        painter.setBrush(Qt.NoBrush)
        painter.drawLine(
            QPointF(size * 0.59, size * 0.11),
            QPointF(size * 0.59, size * 0.31),
        )
        painter.drawLine(
            QPointF(size * 0.59, size * 0.31),
            QPointF(size * 0.78, size * 0.31),
        )
        painter.drawLine(
            QPointF(size * 0.38, size * 0.5),
            QPointF(size * 0.66, size * 0.5),
        )
        painter.drawLine(
            QPointF(size * 0.38, size * 0.66),
            QPointF(size * 0.61, size * 0.66),
        )
    elif kind == "star":
        points = []
        center = QPointF(size / 2, size / 2)
        for index in range(10):
            angle = -math.pi / 2 + index * math.pi / 5
            radius = size * (0.38 if index % 2 == 0 else 0.17)
            points.append(
                QPointF(
                    center.x() + math.cos(angle) * radius,
                    center.y() + math.sin(angle) * radius,
                )
            )
        painter.setBrush(fill)
        painter.drawPolygon(QPolygonF(points))
    elif kind == "clock":
        painter.setBrush(fill)
        painter.drawEllipse(QRectF(size * 0.13, size * 0.13, size * 0.74, size * 0.74))
        painter.setBrush(Qt.NoBrush)
        painter.drawLine(
            QPointF(size * 0.5, size * 0.28),
            QPointF(size * 0.5, size * 0.52),
        )
        painter.drawLine(
            QPointF(size * 0.5, size * 0.52),
            QPointF(size * 0.68, size * 0.62),
        )
    else:
        painter.setBrush(fill)
        for index, width in enumerate((0.68, 0.58, 0.72)):
            painter.drawRoundedRect(
                QRectF(size * 0.15, size * (0.2 + index * 0.24), size * width, size * 0.13),
                size * 0.06,
                size * 0.06,
            )

    painter.end()
    return QIcon(pixmap)
