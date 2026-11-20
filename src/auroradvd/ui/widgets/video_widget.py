"""
Área de reproducción de AuroraDVD.
"""

from PySide6.QtCore import QSize, QTimer, Qt
from PySide6.QtGui import QCursor, QResizeEvent
from PySide6.QtWidgets import QLabel, QStackedLayout, QWidget

from auroradvd.ui.widgets.playback_controls import PlaybackControls


class VideoWidget(QWidget):
    """Superficie de video y mensaje de espera."""

    def __init__(self, controls: PlaybackControls) -> None:
        super().__init__()
        self._fullscreen = False
        self._controls = controls
        controls.setParent(self)
        controls.setAttribute(Qt.WidgetAttribute.WA_NativeWindow)

        self._hover_timer = QTimer(self)
        self._hover_timer.setInterval(75)
        self._hover_timer.timeout.connect(self._update_control_visibility)

        self._placeholder = QLabel("AuroraDVD\n\nNo hay ningún DVD cargado.")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._surface = QWidget()
        self._surface.setAttribute(Qt.WidgetAttribute.WA_NativeWindow)
        self._surface.setStyleSheet("background-color: #1e1e1e;")

        self._placeholder.setStyleSheet(
            "background-color: #1e1e1e; color: white; font-size: 18px;"
        )

        self._layout = QStackedLayout(self)
        self._layout.addWidget(self._placeholder)
        self._layout.addWidget(self._surface)
        self._position_controls()

    def minimumSizeHint(self) -> QSize:
        size = super().minimumSizeHint()
        size.setWidth(max(size.width(), self._controls.minimumSizeHint().width()))
        return size

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._position_controls()

    def set_fullscreen(self, fullscreen: bool) -> None:
        self._fullscreen = fullscreen
        self._controls.set_fullscreen(fullscreen)
        self._controls.setVisible(not fullscreen)
        self._position_controls()
        if fullscreen:
            self._hover_timer.start()
        else:
            self._hover_timer.stop()

    def _position_controls(self) -> None:
        height = self._controls.sizeHint().height()
        self._layout.setContentsMargins(0, 0, 0, 0 if self._fullscreen else height)
        self._controls.setGeometry(0, self.height() - height, self.width(), height)
        self._controls.raise_()

    def _update_control_visibility(self) -> None:
        # VLC can own the native child under the cursor and receive its mouse
        # events directly. Poll only while fullscreen and the window is active.
        if not self._fullscreen:
            return
        cursor = self.mapFromGlobal(QCursor.pos())
        shown = not self._controls.isHidden()
        at_edge = self.rect().contains(cursor) and cursor.y() >= self.height() - 22
        over_controls = shown and self._controls.geometry().contains(cursor)
        in_popup = self._controls.has_open_selector()
        visible = in_popup or (self.window().isActiveWindow() and (at_edge or over_controls))
        if visible != shown:
            self._controls.setVisible(visible)
            if visible:
                self._controls.raise_()

    def show_video(self) -> int:
        self._layout.setCurrentWidget(self._surface)
        self._controls.raise_()
        return int(self._surface.winId())

    def show_placeholder(self) -> None:
        self._layout.setCurrentWidget(self._placeholder)
