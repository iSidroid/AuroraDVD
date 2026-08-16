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

from PySide6.QtCore import QStorageInfo

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
    
    def has_media(self, drive: Path) -> bool:
        """
        Determina si existe un medio insertado en la unidad óptica.

        Args:
            drive: Ruta de la unidad óptica, por ejemplo E:\\

        Returns:
            True si existe un medio disponible.
            False si la unidad está vacía o no está lista.
        """

        storage = QStorageInfo(str(drive))

        return storage.isValid() and storage.isReady()


    def is_dvd_video(self, drive: Path) -> bool:
        """
        Determina si la unidad contiene una estructura DVD-Video válida.

        Args:
            drive: Ruta de la unidad óptica, por ejemplo E:\\

        Returns:
            True si existe una estructura DVD-Video básica.
            False en caso contrario.
        """

        video_ts = drive / "VIDEO_TS"

        return (
            video_ts.is_dir()
            and (video_ts / "VIDEO_TS.IFO").is_file()
            and (video_ts / "VIDEO_TS.BUP").is_file()
        )

    def get_media_info(self, drive: Path) -> dict[str, object]:
        """
        Obtiene información básica del medio insertado.

        Args:
            drive: Ruta de la unidad óptica, por ejemplo E:\\

        Returns:
            Diccionario con información del medio.
        """

        storage = QStorageInfo(str(drive))

        if not storage.isValid() or not storage.isReady():
            return {
                "drive": drive,
                "label": "",
                "ready": False,
                "size": 0,
                "is_dvd_video": False,
            }

        return {
            "drive": drive,
            "label": storage.displayName(),
            "ready": True,
            "size": storage.bytesTotal(),
            "is_dvd_video": self.is_dvd_video(drive),
        }

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