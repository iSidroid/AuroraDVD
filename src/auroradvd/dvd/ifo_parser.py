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

from csv import reader
from pathlib import Path
from auroradvd.dvd.binary_reader import BinaryReader
from auroradvd.dvd.models import IfoHeader, IfoType



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


    def parse_header(self) -> IfoHeader:
        """
        Lee y representa la cabecera básica de un archivo IFO.

        Returns:
            IfoHeader con la información básica detectada.

        Raises:
            ValueError: si el identificador no corresponde a un IFO válido.
            OSError: si el archivo no puede leerse.
        """
        reader = BinaryReader(self.path)
        identifier = reader.read_bytes(0, 12)

        if identifier == self.DVD_VIDEO_VMG_MAGIC:
            ifo_type = IfoType.VMG
        elif identifier == self.DVD_VIDEO_VTS_MAGIC:
            ifo_type = IfoType.VTS
        else:
            raise ValueError("Identificador IFO no válido")

        last_sector_set = reader.read_uint32_be(0x0C)
        last_sector_ifo = reader.read_uint32_be(0x1C)
        version = reader.read_uint16_be(0x20)

        return IfoHeader(
            identifier=identifier.decode("ascii"),
            type=ifo_type,
            last_sector_set=last_sector_set,
            last_sector_ifo=last_sector_ifo,
            version=version,
        )

    def is_valid(self) -> bool:
        """
        Determina si el archivo contiene una cabecera IFO válida.

        Returns:
            True si la cabecera corresponde a DVD-Video.
        """

        return self.get_type() is not None