"""
AuroraDVD

Archivo:
application.py

Descripción:
Punto de entrada principal de la aplicación.

Autor:
Isidro Riquelme

Versión:
0.1.0-dev
"""

import sys

from PySide6.QtWidgets import QApplication

from auroradvd.ui.main_window import MainWindow


def main() -> int:
    """
    Inicia la aplicación AuroraDVD.
    """

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())