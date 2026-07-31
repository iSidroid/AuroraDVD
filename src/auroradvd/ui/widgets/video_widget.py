"""
Área de reproducción de AuroraDVD.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class VideoWidget(QWidget):
    """
    Widget donde se mostrará el video.

    En futuras versiones contendrá el reproductor VLC.
    """

    def __init__(self) -> None:
        super().__init__()

        self._build_ui()

    def _build_ui(self) -> None:

        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
            }

            QLabel {
                color: white;
                font-size: 18px;
            }
        """)

        label = QLabel(
            "AuroraDVD\n\nNo hay ningún DVD cargado."
        )
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(label)

        self.setLayout(layout)