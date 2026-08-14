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

#from PySide6.QtCore import Qt (V.1.0.0)
from auroradvd.ui.actions import ApplicationActions
from auroradvd.ui.menu_bar import MenuBar

#from PySide6.QtWidgets import QLabel, QMainWindow, QStatusBar 
from PySide6.QtWidgets import QApplication, QMainWindow
from auroradvd.core.constants import (
    APP_NAME,
    DEFAULT_HEIGHT,
    DEFAULT_WIDTH,
)

from auroradvd.ui.widgets.video_widget import VideoWidget
from auroradvd.ui.status_bar import StatusBar
from auroradvd.ui.tool_bar import ToolBar


class MainWindow(QMainWindow):
    """
    Ventana principal de AuroraDVD.
    """

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle(APP_NAME)
        self.resize(DEFAULT_WIDTH, DEFAULT_HEIGHT)
        self._actions = ApplicationActions()
        self._actions.exit.triggered.connect(QApplication.quit)
        self._actions.open_dvd.triggered.connect(self._open_dvd)
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

        #con estos cambios se elimina esos "textos mágicos" en main window
    def _open_dvd(self) -> None: #Metodo para abrir los DVD
        """
        Maneja la acción de abrir un DVD.
        """
        self._status_bar.showMessage("Abrir DVD seleccionado")
