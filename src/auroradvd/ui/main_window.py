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

from auroradvd.ui.actions import ApplicationActions
from auroradvd.ui.menu_bar import MenuBar

from PySide6.QtWidgets import QApplication, QMainWindow
from auroradvd.core.constants import (
    APP_NAME,
    DEFAULT_HEIGHT,
    DEFAULT_WIDTH,
)

from auroradvd.ui.widgets.video_widget import VideoWidget
from auroradvd.ui.status_bar import StatusBar
from auroradvd.ui.tool_bar import ToolBar
from auroradvd.ui.dialogs.dvd_dialog import DvdDialog
from auroradvd.services.optical_drive_service import OpticalDriveService

class MainWindow(QMainWindow):
    """
    Ventana principal de AuroraDVD.
    """

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle(APP_NAME)
        self.resize(DEFAULT_WIDTH, DEFAULT_HEIGHT)
        self._actions = ApplicationActions()
        self._optical_drive_service = OpticalDriveService()
        self._actions.exit.triggered.connect(QApplication.quit)
        self._actions.open_dvd.triggered.connect(self._open_dvd)
        self._actions.eject_drive.triggered.connect(self._eject_drive)
        self._actions.close_tray.triggered.connect(self._close_tray)
        self._build_ui()
    

    
    def _build_ui(self) -> None:
        """
        Construye la interfaz principal.
        """

        self.setMenuBar(MenuBar(self._actions))
        self._video_widget = VideoWidget()
        self.setCentralWidget(self._video_widget)
        self.addToolBar(ToolBar(self._actions))


        self._status_bar = StatusBar()
        self.setStatusBar(self._status_bar)


    def _open_dvd(self) -> None:
        """
        Abre el diálogo de selección de DVD.
        """

        dialog = DvdDialog(self)

        if dialog.exec():
            self._status_bar.showMessage("DVD seleccionado")

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

        if self._optical_drive_service.eject(drive):
            self._status_bar.showMessage(
                f"Bandeja abierta: {drive}"
            )
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
        else:
            self._status_bar.showMessage(
                f"No se pudo cerrar la bandeja: {drive}"
            )
            