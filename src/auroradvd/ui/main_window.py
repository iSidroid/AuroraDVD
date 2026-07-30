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

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMainWindow, QStatusBar


class MainWindow(QMainWindow):
    """
    Ventana principal de AuroraDVD.
    """

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("AuroraDVD")
        self.resize(1100, 700)

        self._build_ui()

    def _build_ui(self) -> None:
        """
        Construye la interfaz principal.
        """

        label = QLabel("Bienvenido a AuroraDVD")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.setCentralWidget(label)

        status = QStatusBar()
        status.showMessage("Estado: Listo")

        self.setStatusBar(status)