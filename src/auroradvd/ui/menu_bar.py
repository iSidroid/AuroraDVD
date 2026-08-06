"""
AuroraDVD
==========

Módulo:
    menu_bar

Responsabilidad:
    Contiene la barra de menús principal de la aplicación.

Autor:
    Isidro Riquelme
"""

from PySide6.QtWidgets import QMenuBar

from auroradvd.ui.actions import ApplicationActions


class MenuBar(QMenuBar):
    """
    Barra de menús principal de AuroraDVD.
    """

    def __init__(self, actions: ApplicationActions) -> None:
        super().__init__()

        self._actions = actions

        self._build_ui()

    def _build_ui(self) -> None:
        """
        Construye la barra de menús.
        """

        file_menu = self.addMenu("&Archivo")

        file_menu.addAction(self._actions.open_dvd)
        file_menu.addAction(self._actions.open_iso)
        file_menu.addAction(self._actions.open_ts)
        file_menu.addSeparator()
        file_menu.addAction(self._actions.exit)