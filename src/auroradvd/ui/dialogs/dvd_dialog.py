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

from pathlib import Path

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

    def __init__(self, parent=None, *, drives: list[Path]) -> None:
        super().__init__(parent)

        self.setWindowTitle("Abrir DVD")

        self._build_ui(drives)

    @property
    def selected_drive(self) -> Path | None:
        return self._drive_combo.currentData()

    def _build_ui(self, drives: list[Path]) -> None:
        """
        Construye la interfaz del diálogo.
        """

        self._drive_combo = QComboBox()

        for drive in drives:
            self._drive_combo.addItem(str(drive), drive)
        if not drives:
            self._drive_combo.addItem("No se encontró ninguna unidad óptica")
            self._drive_combo.setEnabled(False)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )

        buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(bool(drives))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QFormLayout()

        layout.addRow("Unidad DVD:", self._drive_combo)
        layout.addRow(buttons)

        self.setLayout(layout)