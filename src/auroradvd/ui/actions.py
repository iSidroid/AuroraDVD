"""
AuroraDVD
==========

Módulo:
    actions

Responsabilidad:
    Contiene las acciones principales de la aplicación.

Autor:
    Isidro Riquelme
"""

from PySide6.QtGui import QAction


class ApplicationActions:
    """
    Acciones globales de AuroraDVD.
    """

    def __init__(self) -> None:

        self._build_actions()

    def _build_actions(self) -> None:
        """
        Crea todas las acciones de la aplicación.
        """

        self._open_dvd = QAction("Abrir DVD...")
        self._open_dvd.setStatusTip("Abre un DVD desde una unidad óptica")

        self._open_iso = QAction("Abrir imagen ISO...")
        self._open_iso.setStatusTip("Abre una imagen ISO")

        self._open_ts = QAction("Abrir VIDEO_TS")
        self._open_ts.setStatusTip("Abre una carpeta VIDEO_TS")

        self._exit = QAction("Salir")
        self._exit.setStatusTip("Cierra AuroraDVD")

    @property
    def open_dvd(self) -> QAction:
        return self._open_dvd


    @property
    def open_iso(self) -> QAction:
        return self._open_iso

    @property
    def open_ts(self)-> QAction:
        return self._open_ts
    
    @property
    def exit(self) -> QAction:
        return self._exit

