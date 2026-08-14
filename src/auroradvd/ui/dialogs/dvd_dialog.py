"""
AuroraDVD
==========

Módulo:
    dvd_dialog

Responsabilidad:
    Diálogo para seleccionar una unidad DVD.

Autor:
    Isidro Riquelme
"""

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
)


class DvdDialog(QDialog):
    """
    Diálogo para seleccionar una unidad DVD.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Abrir DVD")

        self._build_ui()

    def _build_ui(self) -> None:
        """
        Construye la interfaz del diálogo.
        """

        self._drive_combo = QComboBox()

        self._drive_combo.addItem("Detectando unidades...")

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QFormLayout()

        layout.addRow("Unidad DVD:", self._drive_combo)
        layout.addRow(buttons)

        self.setLayout(layout)