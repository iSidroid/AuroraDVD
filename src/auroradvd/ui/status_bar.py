"""
AuroraDVD
==========

Módulo:
    status_bar

Responsabilidad:
    Barra de estado principal de AuroraDVD.

Autor:
    Isidro Riquelme
"""

from PySide6.QtWidgets import QLabel, QStatusBar

from auroradvd.core.constant import STATUS_READY


class StatusBar(QStatusBar):
    """
    Barra de estado principal.
    """

    def __init__(self) -> None:
        super().__init__()

        self._build_ui()
        self._initialize()

    def _build_ui(self) -> None:
        """
        Construye la barra de estado.
        """

        self._status_label = QLabel(STATUS_READY)

        self.addWidget(self._status_label)

    def _initialize(self) -> None:
        """
        Inicializa el estado de la barra.
        """
        pass

    def set_status(self, message: str) -> None:
        """
        Actualiza el mensaje de estado.
        """

        self._status_label.setText(message)