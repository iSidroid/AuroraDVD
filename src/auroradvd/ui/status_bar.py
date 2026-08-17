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

from auroradvd.core.constants import STATUS_READY


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

    def set_media_info(
        self,
        *,
        drive: str,
        label: str,
        size: int,
        is_dvd_video: bool,
    ) -> None:
        """
        Muestra información básica del medio insertado.
        """

        size_gb = size / (1024 ** 3)
        media_type = "DVD-Video" if is_dvd_video else "DVD de datos"

        self._status_label.setText(
            f"{media_type} | {label} | {drive} | {size_gb:.2f} GB"
        )

    def clear_media_info(self) -> None:
        """
        Muestra el estado correspondiente a una unidad sin medio.
        """

        self._status_label.setText("No hay ningún medio insertado")        