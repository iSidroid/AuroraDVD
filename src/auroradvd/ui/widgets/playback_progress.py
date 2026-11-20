"""Title timeline with a preview that stays stable during dragging."""

from PySide6.QtCore import QSignalBlocker, Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QSlider, QWidget

from auroradvd.player.playback_status import PlaybackState, PlaybackStatus


def format_time(milliseconds: int | None) -> str:
    if milliseconds is None:
        return "--:--:--"
    seconds = max(0, milliseconds) // 1000
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


class PlaybackProgress(QWidget):
    seek_requested = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self.elapsed = QLabel("00:00:00")
        self.duration = QLabel("--:--:--")
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setAccessibleName("Posición de reproducción")
        self.slider.setRange(0, 10000)
        self.slider.setEnabled(False)
        self._status = PlaybackStatus()
        self._drag_title = None
        self.slider.sliderPressed.connect(self._begin_drag)
        self.slider.sliderReleased.connect(self._end_drag)
        self.slider.valueChanged.connect(self._changed)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.elapsed)
        layout.addWidget(self.slider, 1)
        layout.addWidget(self.duration)

    def _begin_drag(self) -> None:
        self._drag_title = self._status.title

    def _end_drag(self) -> None:
        valid = self._drag_title == self._status.title
        self._drag_title = None
        if valid:
            self._send_seek()

    def _changed(self, value: int) -> None:
        duration = self._status.duration_ms
        if duration is None:
            return
        self.elapsed.setText(format_time(value * duration // 10000))
        if not self.slider.isSliderDown():
            self._send_seek()

    def _send_seek(self) -> None:
        if self.slider.isEnabled() and self._status.duration_ms is not None:
            self.seek_requested.emit(self.slider.value() * self._status.duration_ms // 10000)

    def update_status(self, status: PlaybackStatus) -> None:
        previous_title = self._status.title
        self._status = status
        active = status.state in (PlaybackState.PLAYING, PlaybackState.PAUSED)
        enabled = active and status.seekable and status.duration_ms is not None
        if previous_title != status.title or not enabled:
            self._drag_title = None
            self.slider.setSliderDown(False)
        self.slider.setEnabled(enabled)
        self.duration.setText(format_time(status.duration_ms))
        if self.slider.isSliderDown():
            return
        elapsed = status.elapsed_ms if active else 0
        self.elapsed.setText(format_time(elapsed))
        value = 0
        if status.duration_ms and elapsed is not None:
            value = max(0, min(10000, elapsed * 10000 // status.duration_ms))
        with QSignalBlocker(self.slider):
            self.slider.setValue(value)
