"""Welcome page kept separate from the native VLC video surface."""

from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPaintEvent
from PySide6.QtWidgets import QWidget

from auroradvd.resources.branding import welcome_logo


class WelcomeWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._logo = welcome_logo()
        self.setAccessibleName("Bienvenido a AuroraDVD")
        self.setMinimumSize(120, 120)

    def logo_rect(self) -> QRect:
        if self._logo.isNull():
            return QRect()
        available = self.rect().adjusted(32, 32, -32, -32).size()
        available = QSize(max(0, available.width()), max(0, available.height()))
        limit = available.boundedTo(QSize(420, 420))
        size = self._logo.size().scaled(limit, Qt.AspectRatioMode.KeepAspectRatio)
        target = QRect(0, 0, size.width(), size.height())
        target.moveCenter(self.rect().center())
        return target

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#000000"))
        if self._logo.isNull():
            painter.setPen(QColor("white"))
            painter.drawText(
                self.rect(), Qt.AlignmentFlag.AlignCenter,
                "AuroraDVD\n\nNo hay ningún DVD cargado.",
            )
            return
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.drawPixmap(self.logo_rect(), self._logo, self._logo.rect())
