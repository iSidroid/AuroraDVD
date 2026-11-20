"""Paths for the official application artwork."""

from pathlib import Path

from PySide6.QtGui import QIcon, QPixmap


LOGO_PATH = Path(__file__).resolve().parent / "auroradvd.png"
ICON_PATH = LOGO_PATH.with_suffix(".ico")


def application_icon() -> QIcon:
    path = ICON_PATH if ICON_PATH.is_file() else LOGO_PATH
    return QIcon(str(path)) if path.is_file() else QIcon()


def welcome_logo() -> QPixmap:
    return QPixmap(str(LOGO_PATH)) if LOGO_PATH.is_file() else QPixmap()
