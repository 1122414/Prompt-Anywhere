from PySide6.QtCore import QRect, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.ui.theme import (
    current_palette,
    current_theme,
    current_theme_asset,
    current_theme_variant,
    palette_for_theme,
    theme_asset,
    theme_display_label,
)


def _cover_source_rect(pixmap: QPixmap, target: QRect, anchor_right: bool = True) -> QRect:
    target_ratio = target.width() / max(1, target.height())
    source_ratio = pixmap.width() / max(1, pixmap.height())
    if source_ratio > target_ratio:
        source_width = int(pixmap.height() * target_ratio)
        source_x = pixmap.width() - source_width if anchor_right else (
            pixmap.width() - source_width
        ) // 2
        return QRect(source_x, 0, source_width, pixmap.height())
    source_height = int(pixmap.width() / target_ratio)
    source_y = max(0, (pixmap.height() - source_height) // 2)
    return QRect(0, source_y, pixmap.width(), source_height)


class ThemeHeader(QWidget):
    def __init__(self, title: str, subtitle: str, compact: bool = False, parent=None):
        super().__init__(parent)
        self._title_text = title
        self._subtitle_text = subtitle
        self._compact = compact
        self._pixmap = QPixmap()
        self.setObjectName("themeHeader")
        self.setFixedHeight(64 if compact else 104)
        self._setup_ui()
        self.apply_theme()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(22, 12, 18, 12)
        layout.setSpacing(12)
        text_layout = QVBoxLayout()
        text_layout.setSpacing(3)
        self.title_label = QLabel(self._title_text)
        self.title_label.setObjectName("brandTitle")
        self.subtitle_label = QLabel(self._subtitle_text)
        self.subtitle_label.setObjectName("brandCaption")
        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.subtitle_label)
        self.theme_badge = QLabel()
        self.theme_badge.setObjectName("themeBadge")
        text_layout.addWidget(self.theme_badge, 0, Qt.AlignLeft)
        layout.addLayout(text_layout)
        layout.addStretch()

    def apply_theme(self):
        palette = current_palette()
        asset = current_theme_asset()
        self._pixmap = QPixmap(str(asset)) if asset else QPixmap()
        theme_id = current_theme()
        self.theme_badge.setText(
            theme_display_label(theme_id, current_theme_variant(theme_id))
        )
        self.title_label.setStyleSheet(
            f"color: {palette['ink']}; font-size: {'15px' if self._compact else '19px'}; font-weight: 700;"
        )
        self.subtitle_label.setStyleSheet(
            f"color: {palette['muted']}; font-size: 11px;"
        )
        self.theme_badge.setStyleSheet(
            f"""
            color: {palette["accent_hover"]};
            background: {palette["surface_active"]};
            border: 1px solid {palette["hairline_strong"]};
            border-radius: 9px;
            padding: 2px 8px;
            font-size: 11px;
            """
        )
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        palette = current_palette()
        frame = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
        clip = QPainterPath()
        clip.addRoundedRect(frame, 16, 16)
        painter.setClipPath(clip)
        painter.fillRect(self.rect(), QColor(palette["surface_panel"]))
        if not self._pixmap.isNull():
            art_rect = QRect(
                int(self.width() * 0.38),
                0,
                max(1, int(self.width() * 0.62)),
                self.height(),
            )
            source = _cover_source_rect(self._pixmap, art_rect)
            painter.setOpacity(0.9)
            painter.drawPixmap(art_rect, self._pixmap, source)
            painter.setOpacity(1.0)
            overlay = QLinearGradient(0, 0, self.width(), 0)
            base = QColor(palette["surface_panel"])
            base.setAlpha(248)
            transparent = QColor(base)
            transparent.setAlpha(96)
            overlay.setColorAt(0.0, base)
            overlay.setColorAt(0.46, base)
            overlay.setColorAt(0.72, transparent)
            overlay.setColorAt(1.0, QColor(7, 17, 31, 32))
            painter.fillRect(self.rect(), overlay)
        painter.setClipping(False)
        painter.setPen(QPen(QColor(palette["hairline_strong"]), 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(frame, 16, 16)
        painter.end()
        super().paintEvent(event)


class ThemeVariantPreview(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._theme_id = "light"
        self._variant_id = ""
        self._palette = palette_for_theme("light")
        self._pixmap = QPixmap()
        self.setMinimumHeight(152)

    def set_theme(self, theme_id: str, variant_id: str = ""):
        self._theme_id = theme_id
        self._variant_id = variant_id
        self._palette = palette_for_theme(theme_id, variant_id)
        asset = theme_asset(theme_id, variant_id)
        self._pixmap = QPixmap(str(asset)) if asset else QPixmap()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        frame = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
        path = QPainterPath()
        path.addRoundedRect(frame, 12, 12)
        painter.setClipPath(path)
        painter.fillRect(self.rect(), QColor(self._palette["surface"]))

        if not self._pixmap.isNull():
            source = _cover_source_rect(self._pixmap, self.rect())
            painter.setOpacity(0.9)
            painter.drawPixmap(self.rect(), self._pixmap, source)
            painter.setOpacity(1.0)
            overlay = QLinearGradient(0, 0, self.width(), 0)
            deep = QColor(self._palette["canvas"])
            deep.setAlpha(242)
            soft = QColor(deep)
            soft.setAlpha(150)
            clear = QColor(deep)
            clear.setAlpha(18)
            overlay.setColorAt(0.0, deep)
            overlay.setColorAt(0.48, soft)
            overlay.setColorAt(1.0, clear)
            painter.fillRect(self.rect(), overlay)
        else:
            gradient = QLinearGradient(0, 0, self.width(), self.height())
            gradient.setColorAt(0.0, QColor(self._palette["surface_panel"]))
            gradient.setColorAt(1.0, QColor(self._palette["surface_active"]))
            painter.fillRect(self.rect(), gradient)
            colors = (
                self._palette["primary"],
                self._palette["accent"],
                self._palette["highlight"],
            )
            for index, color in enumerate(colors):
                painter.setBrush(QColor(color))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(
                    self.width() - 54 - index * 34,
                    self.height() - 48 - index * 10,
                    28,
                    28,
                )

        painter.setClipping(False)
        painter.setPen(QColor(self._palette["ink"]))
        title_font = QFont("Segoe UI", 15)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.drawText(
            QRect(20, 25, max(120, self.width() - 40), 30),
            Qt.AlignLeft | Qt.AlignVCenter,
            "Prompt Anywhere",
        )
        painter.setPen(QColor(self._palette["muted"]))
        painter.setFont(QFont("Microsoft YaHei UI", 10))
        painter.drawText(
            QRect(20, 60, max(120, self.width() - 40), 26),
            Qt.AlignLeft | Qt.AlignVCenter,
            theme_display_label(self._theme_id, self._variant_id),
        )
        painter.setPen(QPen(QColor(self._palette["hairline_strong"]), 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(frame, 12, 12)
        painter.end()
        super().paintEvent(event)
