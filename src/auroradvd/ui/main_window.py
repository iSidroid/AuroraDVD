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


#from PySide6.QtWidgets import QLabel, QMainWindow, QStatusBar 
from PySide6.QtWidgets import QMainWindow, QStatusBar #(se eliminó QLabel)
from auroradvd.core.constant import (
    APP_NAME,
    DEFAULT_HEIGHT,
    DEFAULT_WIDTH,
)

from auroradvd.ui.widgets.video_widget import VideoWidget
from auroradvd.ui.status_bar import StatusBar

class MainWindow(QMainWindow):
    """
    Ventana principal de AuroraDVD.
    """

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle(APP_NAME)
        self.resize(DEFAULT_WIDTH, DEFAULT_HEIGHT)

        self._build_ui()

    def _build_ui(self) -> None:
        """
        Construye la interfaz principal.
        """
        ###Se eliminó mensaje que usaba QlLabel###
        #label = QLabel("Bienvenido a AuroraDVD")
        #label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._video_widget = VideoWidget()
        self.setCentralWidget(self._video_widget)
       # self.setCentralWidget(label)

       # status = QStatusBar()
       # status.showMessage("Estado: Listo")
       # self.setStatusBar(status)

        self._status_bar = StatusBar()
        self.setStatusBar(self._status_bar)

        #con estos cabios se elimina esos "textos mágicos" en main window

