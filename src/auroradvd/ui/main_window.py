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
from PySide6.QtWidgets import (
    QApplication, QAbstractButton, QComboBox, QLineEdit, QMainWindow, QMessageBox,
    QSlider, QSpinBox, QTextEdit, QPlainTextEdit,
)

from auroradvd.resources.branding import application_icon
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
    _seek_requested = Signal(int, int, object)
    _mute_requested = Signal(bool)

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(application_icon())
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
        self._bind_actions()
        QApplication.instance().installEventFilter(self)

    def _bind_actions(self) -> None:
        actions = self._actions
        controls = self._controls
        pairs = (
            (actions.play, controls.play_button, controls.play_requested),
            (actions.pause, controls.pause_button, None),
            (actions.resume, controls.resume_button, None),
            (actions.stop, controls.stop_button, controls.stop_requested),
            (actions.previous, controls.previous_button, None),
            (actions.next, controls.next_button, None),
            (actions.fullscreen, controls.fullscreen_button, controls.fullscreen_requested),
        )
        for action, button, signal in pairs:
            button.clicked.disconnect()
            button.clicked.connect(action.trigger)
            if signal is not None:
                action.triggered.connect(signal)
            self.addAction(action)
        actions.pause.triggered.connect(lambda: controls.pause_requested.emit(True))
        actions.resume.triggered.connect(lambda: controls.pause_requested.emit(False))
        actions.previous.triggered.connect(lambda: controls.chapter_step_requested.emit(-1))
        actions.next.triggered.connect(lambda: controls.chapter_step_requested.emit(1))
        actions.pause_resume.triggered.connect(self._toggle_pause)
        actions.mute.toggled.connect(self._mute_requested)
        self.addAction(actions.open_dvd)
        self.addAction(actions.mute)
        actions.help.triggered.connect(self._show_help)
        actions.about.triggered.connect(lambda: QMessageBox.about(
            self, "AuroraDVD", "AuroraDVD\nReproductor de DVD para Windows."
        ))
        controls.progress.seek_requested.connect(self._seek)
        self.menuBar().bind_selectors(controls)
        self._sync_actions()

    def _sync_actions(self) -> None:
        for action, button in (
            (self._actions.play, self._controls.play_button),
            (self._actions.pause, self._controls.pause_button),
            (self._actions.resume, self._controls.resume_button),
            (self._actions.stop, self._controls.stop_button),
            (self._actions.previous, self._controls.previous_button),
            (self._actions.next, self._controls.next_button),
        ):
            action.setEnabled(button.isEnabled())
        self._actions.pause_resume.setEnabled(
            self._actions.pause.isEnabled() or self._actions.resume.isEnabled()
        )
        self.menuBar().update_selectors()

    def _toggle_pause(self) -> None:
        if self._actions.pause.isEnabled():
            self._actions.pause.trigger()
        elif self._actions.resume.isEnabled():
            self._actions.resume.trigger()

    def eventFilter(self, watched, event) -> bool:
        if event.type() not in (QEvent.Type.ShortcutOverride, QEvent.Type.KeyPress):
            return super().eventFilter(watched, event)
        if not self.isActiveWindow() or QApplication.activeModalWidget() is not None:
            return False
        if QApplication.activePopupWidget() is not None or event.modifiers() != Qt.KeyboardModifier.NoModifier:
            return False
        focus = QApplication.focusWidget()
        if isinstance(focus, (QAbstractButton, QComboBox, QLineEdit, QSlider,
                              QSpinBox, QTextEdit, QPlainTextEdit)):
            return False
        action = {
            Qt.Key.Key_Space: self._actions.pause_resume,
            Qt.Key.Key_S: self._actions.stop,
            Qt.Key.Key_M: self._actions.mute,
        }.get(event.key())
        if action is None or not action.isEnabled():
            return False
        event.accept()
        if event.type() == QEvent.Type.KeyPress and not event.isAutoRepeat():
            action.trigger()
        return True

    def _show_help(self) -> None:
        QMessageBox.information(
            self, "Atajos y uso",
            "Ctrl+D  Abrir DVD\nEspacio  Pausar/reanudar\nS  Detener\n"
            "Ctrl+Izquierda / Ctrl+Derecha  Capítulo anterior/siguiente\n"
            "M  Silenciar\nF11  Pantalla completa\nEsc  Salir de pantalla completa\n\n"
            "Arrastra la barra de progreso para buscar dentro del título.\n"
            "Los atajos de una tecla respetan el control que tiene el foco."
        )

    def _seek(self, milliseconds: int) -> None:
        self._seek_requested.emit(
            self._playback_id, self._playback_status.title, milliseconds
        )

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
        self._actions.fullscreen.setChecked(fullscreen)


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
        self._seek_requested.connect(player.seek)
        self._mute_requested.connect(player.set_muted)
        self._mute_requested.emit(self._actions.mute.isChecked())
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
        self._sync_actions()

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
            