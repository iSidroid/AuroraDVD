"""
AuroraDVD
==========

Módulo:
    optical_drive_service

Responsabilidad:
    Proporciona operaciones relacionadas con unidades ópticas.

Autor:
    Isidro Riquelme
"""
import ctypes
from pathlib import Path


class OpticalDriveService:
    """
    Servicio para detectar y controlar unidades ópticas en Windows.
    """

    DRIVE_CDROM = 5

    def get_optical_drives(self) -> list[Path]:
        """
        Devuelve las unidades ópticas disponibles en el sistema.
        """

        drives: list[Path] = []

        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            root = f"{letter}:\\"

            drive_type = ctypes.windll.kernel32.GetDriveTypeW(root)

            if drive_type == self.DRIVE_CDROM:
                drives.append(Path(root))

        return drives

    def eject(self, drive: Path) -> bool:
        """
        Abre la bandeja de la unidad óptica indicada.

        Args:
            drive: Ruta de la unidad óptica, por ejemplo E:\\

        Returns:
            True si Windows acepta la orden.
            False si ocurre un error.
        """

        drive_letter = drive.drive.rstrip(":")

        alias = "auroradvd_cdrom"

        mci_send_string = ctypes.windll.winmm.mciSendStringW

        command = f"open {drive_letter}: type cdaudio alias {alias}"

        result = mci_send_string(
            command,
            None,
            0,
            None,
        )

        if result != 0:
            return False

        result = mci_send_string(
            f"set {alias} door open",
            None,
            0,
            None,
        )

        mci_send_string(
            f"close {alias}",
            None,
            0,
            None,
        )

        return result == 0