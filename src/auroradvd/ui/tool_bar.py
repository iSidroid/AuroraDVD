"""
AuroraDVD
==========

Módulo:
    tool_bar

Responsabilidad:
    Contiene la barra de herramientas principal de la aplicación.

Autor:
    Isidro Riquelme
"""

from PySide6.QtWidgets import QToolBar

from auroradvd.ui.actions import ApplicationActions
from PySide6.QtWidgets import QToolBar, QWidget, QSizePolicy

class ToolBar(QToolBar):
    """
    Barra de herramientas principal de AuroraDVD.
    """

    def __init__(self, actions: ApplicationActions) -> None:
        super().__init__()

        self._actions = actions

        self._build_ui()

    def _build_ui(self) -> None:
        """
        Construye la barra de herramientas.
        """
        self.setWindowTitle("Herramientas")
        self.addAction(self._actions.open_dvd)
        self.addAction(self._actions.open_iso)
        self.addAction(self._actions.open_ts)
        spacer = QWidget()
        spacer.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
    )

        self.addWidget(spacer)
        self.addAction(self._actions.exit)
        