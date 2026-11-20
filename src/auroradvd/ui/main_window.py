"""
AuroraDVD
==========

Módulo:
    main_window

Responsabilidad:
    Contiene la ventana principal de la aplicación.

Autor:
    Isidro Riquelme
"""

from pathlib import Path

from PySide6.QtCore import QEvent, QThread, QTimer, Qt, Signal, Slot
from PySide6.QtGui import QCloseEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import QMainWindow

from auroradvd.player.dvd_player import DvdPlayer
from auroradvd.player.playback_status import PlaybackState, PlaybackStatus
from auroradvd.ui.actions import ApplicationActions
from auroradvd.ui.menu_bar import MenuBar
from auroradvd.core.constants import (
    APP_NAME,
    DEFAULT_HEIGHT,
    DEFAULT_WIDTH,
)

from auroradvd.ui.widgets.playback_controls import PlaybackControls
from auroradvd.ui.widgets.video_widget import VideoWidget
from auroradvd.ui.status_bar import StatusBar
from auroradvd.ui.tool_bar import ToolBar
from auroradvd.ui.dialogs.dvd_dialog import DvdDialog
from auroradvd.services.optical_drive_service import OpticalDriveService

class MainWindow(QMainWindow):
    """
    Ventana principal de AuroraDVD.
    """

    _play_dvd_requested = Signal(int, object, object)
    _stop_dvd_requested = Signal()
    _close_dvd_requested = Signal()
    _pause_requested = Signal(int, bool)
    _volume_requested = Signal(int)
    _chapter_requested = Signal(int, int, int)
    _chapter_step_requested = Signal(int, int, int)
    _track_requested = Signal(int, int, str, int)

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle(APP_NAME)
        self.resize(DEFAULT_WIDTH, DEFAULT_HEIGHT)
        self._actions = ApplicationActions()
        self._optical_drive_service = OpticalDriveService()
        self._dvd_thread: QThread | None = None
        self._dvd_player: DvdPlayer | None = None
        self._playback_id = 0
        self._playing_drive: Path | None = None
        self._last_drive: Path | None = None
        self._playback_status = PlaybackStatus()
        self._was_maximized = False
        self._eject_after_stop: Path | None = None
        self._closing_player = False
        self._actions.exit.triggered.connect(self.close)
        self._actions.open_dvd.triggered.connect(self._open_dvd)
        self._actions.eject_drive.triggered.connect(self._eject_drive)
        self._actions.close_tray.triggered.connect(self._close_tray)
        self._build_ui()
        self._update_media_status()

    

    
    def _build_ui(self) -> None:
        """
        Construye la interfaz principal.
        """

        self.setMenuBar(MenuBar(self._actions))
        self._controls = PlaybackControls()
        self._video_widget = VideoWidget(self._controls)
        self.setCentralWidget(self._video_widget)
        self._toolbar = ToolBar(self._actions)
        self.addToolBar(self._toolbar)

        self._status_bar = StatusBar()
        self.setStatusBar(self._status_bar)
        self._controls.play_requested.connect(self._play_last_dvd)
        self._controls.pause_requested.connect(self._set_paused)
        self._controls.stop_requested.connect(self._request_stop)
        self._controls.volume.valueChanged.connect(self._volume_requested)
        self._controls.chapter_requested.connect(self._select_chapter)
        self._controls.chapter_step_requested.connect(self._step_chapter)
        self._controls.track_requested.connect(self._select_track)
        self._controls.fullscreen_requested.connect(self._toggle_fullscreen)
        self._exit_fullscreen_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        self._exit_fullscreen_shortcut.setEnabled(False)
        self._exit_fullscreen_shortcut.activated.connect(self._exit_fullscreen)

    def _toggle_fullscreen(self) -> None:
        if self.isFullScreen():
            self._exit_fullscreen()
        else:
            self._was_maximized = self.isMaximized()
            self.showFullScreen()

    def _exit_fullscreen(self) -> None:
        if self._was_maximized:
            self.showMaximized()
        else:
            self.showNormal()

    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        if event.type() != QEvent.Type.WindowStateChange:
            return
        fullscreen = self.isFullScreen()
        self.menuBar().setVisible(not fullscreen)
        self._toolbar.setVisible(not fullscreen)
        self._status_bar.setVisible(not fullscreen)
        self._video_widget.set_fullscreen(fullscreen)
        self._exit_fullscreen_shortcut.setEnabled(fullscreen)


    def _open_dvd(self) -> None:
        """
        Abre el diálogo de selección de DVD.
        """

        drives = self._optical_drive_service.get_optical_drives()
        dialog = DvdDialog(self, drives=drives)
        accepted = dialog.exec()
        drive = dialog.selected_drive
        dialog.deleteLater()
        if not accepted:
            return

        if drive is None or not self._optical_drive_service.has_media(drive):
            self._status_bar.set_status(
                "No hay un disco disponible en la unidad seleccionada"
            )
            return

        if not self._closing_player and self._playback_status.state != PlaybackState.STOPPING:
            self._play_dvd(drive)

    @Slot()
    def _play_last_dvd(self) -> None:
        drive = self._last_drive
        if drive is not None and self._optical_drive_service.has_media(drive):
            self._play_dvd(drive)
        else:
            self._open_dvd()

    def _play_dvd(self, drive: Path) -> None:
        if self._dvd_thread is None:
            self._start_dvd_player()

        self._playback_id += 1
        self._playing_drive = drive
        self._last_drive = drive
        self._set_playback_status(PlaybackStatus(state=PlaybackState.OPENING))
        self._actions.open_dvd.setEnabled(False)
        self._status_bar.set_status(f"Abriendo DVD en {drive}…")
        self._play_dvd_requested.emit(
            self._playback_id, drive, self._video_widget.show_video()
        )

    def _start_dvd_player(self) -> None:
        # LibVLC can wait for the native video window while stopping playback.
        # Keep the GUI thread free to process those window messages.
        thread = QThread(self)
        player = DvdPlayer(volume=self._controls.volume.value())
        player.moveToThread(thread)
        self._play_dvd_requested.connect(player.play)
        self._stop_dvd_requested.connect(player.stop)
        self._close_dvd_requested.connect(player.close)
        self._pause_requested.connect(player.set_paused)
        self._volume_requested.connect(player.set_volume)
        self._chapter_requested.connect(player.select_chapter)
        self._chapter_step_requested.connect(player.step_chapter)
        self._track_requested.connect(player.select_track)
        player.playing.connect(self._playback_started)
        player.finished.connect(self._playback_finished)
        player.stopped.connect(self._playback_stopped)
        player.controls_changed.connect(self._apply_player_status)
        player.closed.connect(thread.quit)
        thread.finished.connect(player.deleteLater)
        thread.finished.connect(self._complete_close)
        thread.finished.connect(thread.deleteLater)
        self._dvd_thread = thread
        self._dvd_player = player
        thread.start()

    def _set_playback_status(self, status: PlaybackStatus) -> None:
        self._playback_status = status
        self._controls.update_status(status)

    @Slot(int, object)
    def _apply_player_status(self, playback_id: int, status: PlaybackStatus) -> None:
        if (
            playback_id != self._playback_id
            or self._closing_player
            or self._playback_status.state == PlaybackState.STOPPING
        ):
            return
        self._actions.open_dvd.setEnabled(True)
        if status.state == PlaybackState.PAUSED:
            self._status_bar.set_status("Reproducción pausada.")
        self._set_playback_status(status)

    @Slot(bool)
    def _set_paused(self, paused: bool) -> None:
        self._pause_requested.emit(self._playback_id, paused)

    @Slot(int)
    def _select_chapter(self, chapter: int) -> None:
        self._chapter_requested.emit(self._playback_id, self._playback_status.title, chapter)

    @Slot(int)
    def _step_chapter(self, direction: int) -> None:
        self._chapter_step_requested.emit(self._playback_id, self._playback_status.title, direction)

    @Slot(str, int)
    def _select_track(self, kind: str, track: int) -> None:
        self._track_requested.emit(self._playback_id, self._playback_status.title, kind, track)

    @Slot()
    def _request_stop(self) -> None:
        if self._playing_drive is None or self._playback_status.state == PlaybackState.STOPPING:
            return
        self._set_playback_status(PlaybackStatus(state=PlaybackState.STOPPING))
        self._actions.open_dvd.setEnabled(False)
        self._status_bar.set_status("Deteniendo el DVD…")
        self._stop_dvd_requested.emit()

    @Slot(int, str)
    def _playback_started(self, playback_id: int, message: str) -> None:
        if playback_id != self._playback_id or self._closing_player:
            return
        if self._playback_status.state != PlaybackState.STOPPING:
            self._actions.open_dvd.setEnabled(True)
            self._status_bar.set_status(message)

    @Slot(int, str)
    def _playback_finished(self, playback_id: int, message: str) -> None:
        if playback_id != self._playback_id or self._closing_player:
            return
        if self._playback_status.state != PlaybackState.STOPPING:
            self._reset_playback(message)

    def _reset_playback(self, message: str) -> None:
        self._playing_drive = None
        self._set_playback_status(PlaybackStatus())
        self._actions.open_dvd.setEnabled(True)
        self._video_widget.show_placeholder()
        self._status_bar.set_status(message)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._dvd_thread is None:
            super().closeEvent(event)
            return

        event.ignore()
        if not self._closing_player:
            self._closing_player = True
            self._controls.setEnabled(False)
            self._actions.open_dvd.setEnabled(False)
            self._actions.eject_drive.setEnabled(False)
            self._actions.close_tray.setEnabled(False)
            self._status_bar.set_status("Cerrando el reproductor…")
            self._close_dvd_requested.emit()

    @Slot()
    def _complete_close(self) -> None:
        self._dvd_thread = None
        self._dvd_player = None
        self.close()

    def _eject_drive(self) -> None:
        """
        Abre la bandeja de la primera unidad óptica disponible.
        """

        drives = self._optical_drive_service.get_optical_drives()

        if not drives:
            self._status_bar.showMessage(
                "No se encontró ninguna unidad óptica"
            )
            return

        drive = drives[0]

        if self._playing_drive == drive:
            self._eject_after_stop = drive
            self._actions.open_dvd.setEnabled(False)
            self._actions.eject_drive.setEnabled(False)
            self._actions.close_tray.setEnabled(False)
            self._request_stop()
            return

        self._eject(drive)

    @Slot()
    def _playback_stopped(self) -> None:
        drive = self._eject_after_stop
        self._eject_after_stop = None
        if self._closing_player:
            return

        self._reset_playback("Reproducción detenida.")
        if drive is not None:
            self._actions.eject_drive.setEnabled(True)
            self._actions.close_tray.setEnabled(True)
            self._eject(drive)

    def _eject(self, drive: Path) -> None:
        if self._optical_drive_service.eject(drive):
            if self._last_drive == drive:
                self._last_drive = None
            self._status_bar.showMessage(
                f"Bandeja abierta: {drive}"
            )
            self._update_media_status()    
        else:
            self._status_bar.showMessage(
                f"No se pudo abrir la bandeja: {drive}"
            )

    def _close_tray(self) -> None:
        """
        Cierra la bandeja de la primera unidad óptica disponible.
        """

        drives = self._optical_drive_service.get_optical_drives()

        if not drives:
            self._status_bar.showMessage(
                "No se encontró ninguna unidad óptica"
            )
            return

        drive = drives[0]

        if self._optical_drive_service.close_tray(drive):
            self._status_bar.showMessage(
                f"Bandeja cerrada: {drive}"
            )
            QTimer.singleShot(
                1500,
                self._update_media_status,
            )    
        else:
            self._status_bar.showMessage(
                f"No se pudo cerrar la bandeja: {drive}"
            )

    def _update_media_status(self) -> None:
        """
        Actualiza la barra de estado con la información del medio.
        """

        drives = self._optical_drive_service.get_optical_drives()

        if not drives:
            self._status_bar.set_status(
                "No se encontró ninguna unidad óptica"
            )
            return

        drive = drives[0]

        media_info = self._optical_drive_service.get_media_info(drive)

        if not media_info["ready"]:
            self._status_bar.clear_media_info()
            return

        self._status_bar.set_media_info(
            drive=str(media_info["drive"]),
            label=str(media_info["label"]),
            size=int(media_info["size"]),
            is_dvd_video=bool(media_info["is_dvd_video"]),
        )            
            