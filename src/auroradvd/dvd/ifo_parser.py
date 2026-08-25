"""
AuroraDVD
==========

Módulo:
    ifo_parser

Responsabilidad:
    Lectura y validación inicial de archivos IFO de DVD-Video.

Autor:
    Isidro Riquelme
"""

from pathlib import Path

from auroradvd.dvd.models import IfoType


class IfoParser:
    """
    Parser inicial para archivos IFO de DVD-Video.
    """

    DVD_VIDEO_VMG_MAGIC = b"DVDVIDEO-VMG"
    DVD_VIDEO_VTS_MAGIC = b"DVDVIDEO-VTS"

    def __init__(self, path: Path) -> None:
        self.path = path

    def read_header(self) -> bytes:
        """
        Lee los primeros bytes del archivo IFO.

        Returns:
            Los primeros 12 bytes del archivo.

        Raises:
            FileNotFoundError: si el archivo no existe.
            OSError: si no puede leerse.
        """

        with self.path.open("rb") as file:
            return file.read(12)

    def get_type(self) -> IfoType | None:
        """
        Identifica el tipo de archivo IFO a partir de su identificador.

        Returns:
            IfoType.VMG para VIDEO_TS.IFO.
            IfoType.VTS para un VTS_XX_0.IFO.
            None si el identificador no es válido.
        """

        try:
            header = self.read_header()
        except OSError:
            return None

        if header == self.DVD_VIDEO_VMG_MAGIC:
            return IfoType.VMG

        if header == self.DVD_VIDEO_VTS_MAGIC:
            return IfoType.VTS

        return None

    def is_valid(self) -> bool:
        """
        Determina si el archivo contiene una cabecera IFO válida.

        Returns:
            True si la cabecera corresponde a DVD-Video.
        """

        return self.get_type() is not None