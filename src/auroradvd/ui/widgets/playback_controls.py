"""DVD playback controls shared by regular and fullscreen modes."""

from PySide6.QtCore import QSignalBlocker, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
)

from auroradvd.player.playback_status import PlaybackState, PlaybackStatus
from auroradvd.ui.widgets.playback_progress import PlaybackProgress


class PlaybackControls(QFrame):
    play_requested = Signal()
    pause_requested = Signal(bool)
    stop_requested = Signal()
    chapter_requested = Signal(int)
    chapter_step_requested = Signal(int)
    track_requested = Signal(str, int)
    fullscreen_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setAutoFillBackground(True)
        self.setFrameShape(QFrame.Shape.StyledPanel)

        self.play_button = QPushButton("Reproducir")
        self.pause_button = QPushButton("Pausar")
        self.resume_button = QPushButton("Reanudar")
        self.stop_button = QPushButton("Detener")
        self.previous_button = QPushButton("Anterior")
        self.previous_button.setAccessibleName("Capítulo anterior")
        self.next_button = QPushButton("Siguiente")
        self.next_button.setAccessibleName("Capítulo siguiente")
        self.fullscreen_button = QPushButton("Pantalla completa")

        self.play_button.clicked.connect(self.play_requested)
        self.pause_button.clicked.connect(lambda: self.pause_requested.emit(True))
        self.resume_button.clicked.connect(lambda: self.pause_requested.emit(False))
        self.stop_button.clicked.connect(self.stop_requested)
        self.previous_button.clicked.connect(lambda: self.chapter_step_requested.emit(-1))
        self.next_button.clicked.connect(lambda: self.chapter_step_requested.emit(1))
        self.fullscreen_button.clicked.connect(self.fullscreen_requested)

        self.volume = QSlider(Qt.Orientation.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.setValue(100)
        self.volume.setAccessibleName("Volumen")
        self.volume.setFixedWidth(100)
        self.volume_value = QLabel("100 %")
        self.volume_value.setMinimumWidth(46)
        self.volume.valueChanged.connect(self._show_volume)

        self.chapter = self._new_selector("Capítulo")
        self.audio = self._new_selector("Audio")
        self.video = self._new_selector("Video")
        self.subtitles = self._new_selector("Subtítulos")
        self.video_label = QLabel("Video")
        self.chapter.activated.connect(self._send_chapter)
        self.audio.activated.connect(lambda index: self._send_track("audio", self.audio, index))
        self.video.activated.connect(lambda index: self._send_track("video", self.video, index))
        self.subtitles.activated.connect(
            lambda index: self._send_track("subtitles", self.subtitles, index)
        )

        transport = QHBoxLayout()
        for button in (self.play_button, self.pause_button, self.resume_button, self.stop_button):
            transport.addWidget(button)
        transport.addStretch()
        transport.addWidget(QLabel("Volumen"))
        transport.addWidget(self.volume)
        transport.addWidget(self.volume_value)
        transport.addWidget(self.fullscreen_button)

        navigation = QHBoxLayout()
        navigation.addWidget(self.previous_button)
        navigation.addWidget(QLabel("Capítulo"))
        navigation.addWidget(self.chapter)
        navigation.addWidget(self.next_button)
        navigation.addStretch()
        navigation.addWidget(QLabel("Audio"))
        navigation.addWidget(self.audio)
        navigation.addWidget(self.video_label)
        navigation.addWidget(self.video)
        navigation.addWidget(QLabel("Subtítulos"))
        navigation.addWidget(self.subtitles)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 5, 8, 5)
        layout.setSpacing(4)
        self.progress = PlaybackProgress()
        layout.addWidget(self.progress)
        layout.addLayout(transport)
        layout.addLayout(navigation)
        self.update_status(PlaybackStatus())

    def _new_selector(self, label: str) -> QComboBox:
        combo = QComboBox()
        combo.setAccessibleName(label)
        combo.setMinimumContentsLength(7)
        combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        combo.setMaximumWidth(175)
        return combo

    def _show_volume(self, value: int) -> None:
        self.volume_value.setText(f"{value} %")

    def _send_chapter(self, index: int) -> None:
        self.chapter_requested.emit(self.chapter.itemData(index))

    def _send_track(self, kind: str, combo: QComboBox, index: int) -> None:
        self.track_requested.emit(kind, combo.itemData(index))

    def _update_selector(
        self, combo: QComboBox, options: tuple[tuple[int, str], ...], active: int | None,
        placeholder: str,
    ) -> None:
        items = tuple((combo.itemData(i), combo.itemText(i)) for i in range(combo.count()))
        desired = options or ((None, placeholder),)
        with QSignalBlocker(combo):
            if items != desired:
                combo.clear()
                for item, label in desired:
                    combo.addItem(label, item)
            if options:
                combo.setPlaceholderText("Sin selección")
                combo.setCurrentIndex(combo.findData(active))
            else:
                combo.setCurrentIndex(0)

    def update_status(self, status: PlaybackStatus) -> None:
        for combo in (self.chapter, self.audio, self.video, self.subtitles):
            combo.setProperty("dvdTitle", status.title)
        self.progress.update_status(status)
        state = status.state
        self.play_button.setEnabled(state == PlaybackState.IDLE)
        self.pause_button.setEnabled(state == PlaybackState.PLAYING and status.can_pause)
        self.resume_button.setEnabled(state == PlaybackState.PAUSED)
        self.stop_button.setEnabled(
            state in (PlaybackState.OPENING, PlaybackState.PLAYING, PlaybackState.PAUSED)
        )

        chapters = tuple((number, str(number)) for number in status.chapters)
        self._update_selector(self.chapter, chapters, status.chapter, "Sin capítulos")
        self.chapter.setEnabled(bool(chapters))
        current = status.chapter
        self.previous_button.setEnabled(current is not None and current > status.chapters[0])
        self.next_button.setEnabled(current is not None and current < status.chapters[-1])

        self._update_selector(self.audio, status.audio.options, status.audio.active, "Sin pistas")
        self.audio.setEnabled(len(status.audio.options) > 1)
        self._update_selector(self.video, status.video.options, status.video.active, "Sin pistas")
        multiple_video_tracks = len(status.video.options) > 1
        self.video_label.setVisible(multiple_video_tracks)
        self.video.setVisible(multiple_video_tracks)
        self.video.setEnabled(multiple_video_tracks)
        self._update_selector(
            self.subtitles, status.subtitles.options, status.subtitles.active, "Sin subtítulos"
        )
        self.subtitles.setEnabled(bool(status.subtitles.options))

    def set_fullscreen(self, fullscreen: bool) -> None:
        text = "Salir de pantalla completa" if fullscreen else "Pantalla completa"
        self.fullscreen_button.setText(text)

    def has_open_selector(self) -> bool:
        return any(
            combo.view().isVisible()
            for combo in (self.chapter, self.audio, self.video, self.subtitles)
        )
