"""
AuroraDVD
==========

Módulo:
    binary_reader

Responsabilidad:
    Proporciona operaciones básicas para leer datos binarios.

Autor:
    Isidro Riquelme
"""

from pathlib import Path


class BinaryReader:
    """
    Lector básico de datos binarios.
    """

    def __init__(self, path: Path) -> None:
        self.path = path

    def read_bytes(self, offset: int, size: int) -> bytes:
        """
        Lee una cantidad determinada de bytes desde un offset.

        Args:
            offset: Posición inicial dentro del archivo.
            size: Cantidad de bytes a leer.

        Returns:
            Los bytes solicitados.

        Raises:
            OSError: si el archivo no puede leerse.
            ValueError: si offset o size son negativos.
        """

        if offset < 0:
            raise ValueError("El offset no puede ser negativo")

        if size < 0:
            raise ValueError("El tamaño no puede ser negativo")

        with self.path.open("rb") as file:
            file.seek(offset)
            return file.read(size)

    def read_uint32_be(self, offset: int) -> int:
        """
        Lee un entero sin signo de 32 bits en Big Endian.

        Args:
            offset: Posición inicial dentro del archivo.

        Returns:
            El valor entero representado por los 4 bytes.

        Raises:
            OSError: si el archivo no puede leerse.
            ValueError: si offset es negativo.
        """

        data = self.read_bytes(offset, 4)

        if len(data) != 4:
            raise ValueError("No hay suficientes bytes para leer un uint32")

        return int.from_bytes(data, byteorder="big", signed=False)

    def read_uint16_be(self, offset: int) -> int:
        """
        Lee un entero sin signo de 16 bits en Big Endian.

        Args:
            offset: Posición inicial dentro del archivo.

        Returns:
            El valor entero representado por los 2 bytes.

        Raises:
            OSError: si el archivo no puede leerse.
            ValueError: si offset es negativo o no hay suficientes bytes.
        """

        data = self.read_bytes(offset, 2)

        if len(data) != 2:
            raise ValueError("No hay suficientes bytes para leer un uint16")

        return int.from_bytes(data, byteorder="big", signed=False)           