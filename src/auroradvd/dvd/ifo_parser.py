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
from auroradvd.dvd.binary_reader import BinaryReader
from auroradvd.dvd.constants import DVD_SECTOR_SIZE
from auroradvd.dvd.models import (
    DvdCellPlaybackInfo,
    DvdPgcHeader,
    DvdPgcSearchEntry,
    DvdPgcSearchTable,
    DvdTitlePartSearchEntry,
    DvdTitlePartSearchTable,
    DvdPartOfTitle,
    DvdTitleSearchEntry,
    DvdTitleSearchTable,
    IfoHeader,
    IfoType,
)

class IfoParser:
    """
    Parser inicial para archivos IFO de DVD-Video.
    """

    DVD_VIDEO_VMG_MAGIC = b"DVDVIDEO-VMG"
    DVD_VIDEO_VTS_MAGIC = b"DVDVIDEO-VTS"
    TT_SRPT_POINTER_OFFSET = 0xC4
    TT_SRPT_HEADER_SIZE = 8
    TT_SRPT_ENTRY_SIZE = 12
    VTS_PTT_SRPT_POINTER_OFFSET = 0xC8
    PTT_SRPT_HEADER_SIZE = 8
    PTT_SRPT_OFFSET_ENTRY_SIZE = 4
    PTT_ENTRY_SIZE = 4
    VTS_PGCIT_POINTER_OFFSET = 0xCC
    PGC_HEADER_SIZE = 236
    CELL_PLAYBACK_ENTRY_SIZE = 24

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

    def read_title_search_table(self) -> DvdTitleSearchTable:
        """
        Lee la tabla TT_SRPT de VIDEO_TS.IFO.

        Returns:
            Tabla con las entradas de búsqueda de títulos.

        Raises:
            ValueError: si el archivo o la tabla no son válidos.
            OSError: si no puede leerse el archivo.
        """
        reader = BinaryReader(self.path)

        if self.get_type() != IfoType.VMG:
            raise ValueError(
                "TT_SRPT requiere un archivo VIDEO_TS.IFO válido."
            )

        # El puntero de TT_SRPT está en el offset 0xC4.
        sector = reader.read_uint32_be(
            self.TT_SRPT_POINTER_OFFSET
        )

        if sector == 0:
            raise ValueError("El puntero TT_SRPT es cero.")

        table_offset = reader.sector_to_offset(sector)

        # Leer cabecera de la tabla.
        header = reader.read_bytes(
            table_offset,
            self.TT_SRPT_HEADER_SIZE,
        )

        if len(header) != self.TT_SRPT_HEADER_SIZE:
            raise ValueError("Cabecera TT_SRPT incompleta.")

        title_count = int.from_bytes(header[0:2], "big")
        last_byte = int.from_bytes(header[4:8], "big")

        # last_byte es inclusivo y relativo al inicio de la tabla.
        table_size = last_byte + 1

        if table_size < self.TT_SRPT_HEADER_SIZE:
            raise ValueError("Tamaño TT_SRPT inválido.")

        expected_size = (
            self.TT_SRPT_HEADER_SIZE
            + title_count * self.TT_SRPT_ENTRY_SIZE
        )

        if expected_size > table_size:
            raise ValueError(
                "Las entradas declaradas exceden el tamaño TT_SRPT."
            )

        table_data = reader.read_bytes(table_offset, table_size)

        if len(table_data) != table_size:
            raise ValueError(
                "La tabla TT_SRPT excede los datos disponibles."
            )

        titles = []

        for index in range(title_count):
            start = (
                self.TT_SRPT_HEADER_SIZE
                + index * self.TT_SRPT_ENTRY_SIZE
            )
            entry = table_data[
                start:start + self.TT_SRPT_ENTRY_SIZE
            ]

            titles.append(
                DvdTitleSearchEntry(
                    number=index + 1,
                    playback_type=entry[0],
                    angles=entry[1],
                    chapters=int.from_bytes(entry[2:4], "big"),
                    parental_id=int.from_bytes(entry[4:6], "big"),
                    title_set=entry[6],
                    title_number_in_vts=entry[7],
                    title_set_sector=int.from_bytes(
                        entry[8:12], "big"
                    ),
                )
            )

        return DvdTitleSearchTable(
            offset=table_offset,
            last_byte=last_byte,
            titles=tuple(titles),
        )


    def read_part_of_title_search_table(
        self,
    ) -> DvdTitlePartSearchTable:
        """
        Lee VTS_PTT_SRPT y relaciona cada parte con su PGC
        y número de programa.
        """
        reader = BinaryReader(self.path)

        if self.get_type() != IfoType.VTS:
            raise ValueError(
                "VTS_PTT_SRPT requiere un archivo VTS_XX_0.IFO válido."
            )

        # El puntero de VTS_PTT_SRPT se encuentra en VTSI_MAT.
        sector = reader.read_uint32_be(
            self.VTS_PTT_SRPT_POINTER_OFFSET
        )

        if sector == 0:
            raise ValueError("El puntero VTS_PTT_SRPT es cero.")

        table_offset = reader.sector_to_offset(sector)

        header = reader.read_bytes(
            table_offset,
            self.PTT_SRPT_HEADER_SIZE,
        )

        if len(header) != self.PTT_SRPT_HEADER_SIZE:
            raise ValueError("Cabecera VTS_PTT_SRPT incompleta.")

        title_count = int.from_bytes(header[0:2], "big")
        reserved = int.from_bytes(header[2:4], "big")
        last_byte = int.from_bytes(header[4:8], "big")

        if reserved != 0:
            raise ValueError(
                "Campo reservado de VTS_PTT_SRPT distinto de cero."
            )

        if title_count == 0:
            raise ValueError("VTS_PTT_SRPT no contiene títulos.")

        table_size = last_byte + 1

        offset_table_end = (
            self.PTT_SRPT_HEADER_SIZE
            + title_count * self.PTT_SRPT_OFFSET_ENTRY_SIZE
        )

        if table_size < offset_table_end:
            raise ValueError(
                "La tabla no contiene todos los punteros de títulos."
            )

        table_data = reader.read_bytes(table_offset, table_size)

        if len(table_data) != table_size:
            raise ValueError(
                "VTS_PTT_SRPT excede los datos disponibles."
            )

        # Cada offset es relativo al inicio de VTS_PTT_SRPT.
        title_offsets = [
            int.from_bytes(
                table_data[
                    self.PTT_SRPT_HEADER_SIZE + index * 4:
                    self.PTT_SRPT_HEADER_SIZE + (index + 1) * 4
                ],
                "big",
            )
            for index in range(title_count)
        ]

        titles = []

        for index, title_offset in enumerate(title_offsets):
            next_offset = (
                title_offsets[index + 1]
                if index + 1 < title_count
                else table_size
            )

            if (
                title_offset < offset_table_end
                or next_offset < title_offset
                or next_offset > table_size
            ):
                raise ValueError(
                    f"Offset inválido para el título {index + 1}."
                )

            part_data_size = next_offset - title_offset

            if part_data_size % self.PTT_ENTRY_SIZE != 0:
                raise ValueError(
                    f"Datos incompletos para el título {index + 1}."
                )

            parts = []

            for part_offset in range(
                title_offset,
                next_offset,
                self.PTT_ENTRY_SIZE,
            ):
                pgc_number = int.from_bytes(
                    table_data[part_offset:part_offset + 2],
                    "big",
                )
                program_number = int.from_bytes(
                    table_data[part_offset + 2:part_offset + 4],
                    "big",
                )

                if pgc_number == 0 or program_number == 0:
                    raise ValueError(
                        f"Referencia PGC/programa inválida "
                        f"en el título {index + 1}."
                    )

                parts.append(
                    DvdPartOfTitle(
                        pgc_number=pgc_number,
                        program_number=program_number,
                    )
                )

            titles.append(
                DvdTitlePartSearchEntry(
                    title_number=index + 1,
                    parts=tuple(parts),
                )
            )

        return DvdTitlePartSearchTable(
            offset=table_offset,
            last_byte=last_byte,
            titles=tuple(titles),
        )

    def read_pgc_search_table(self) -> DvdPgcSearchTable:
        """Lee las entradas de búsqueda de VTS_PGCIT."""
        if self.get_type() != IfoType.VTS:
            raise ValueError(
                "VTS_PGCIT solo está disponible en un IFO de tipo VTS"
            )

        reader = BinaryReader(self.path)

        # El puntero de VTS_PGCIT está expresado en sectores.
        sector = reader.read_uint32_be(self.VTS_PGCIT_POINTER_OFFSET)

        if sector == 0:
            raise ValueError("El puntero VTS_PGCIT es cero")

        table_offset = reader.sector_to_offset(sector)

        # Cabecera de VTS_PGCIT: 8 bytes.
        header = reader.read_bytes(table_offset, 8)
        if len(header) != 8:
            raise ValueError("Cabecera VTS_PGCIT incompleta")

        pgc_count = int.from_bytes(header[0:2], "big")
        reserved = int.from_bytes(header[2:4], "big")
        last_byte = int.from_bytes(header[4:8], "big")
        table_size = last_byte + 1

        if reserved != 0:
            raise ValueError("Campo reservado de VTS_PGCIT no válido")

        if table_size < 8:
            raise ValueError("Tamaño VTS_PGCIT no válido")

        search_table_size = 8 + pgc_count * 8
        if search_table_size > table_size:
            raise ValueError(
                "Las entradas de búsqueda exceden el tamaño de VTS_PGCIT"
            )

        entries = []

        for index in range(pgc_count):
            entry_offset = table_offset + 8 + index * 8
            data = reader.read_bytes(entry_offset, 8)

            if len(data) != 8:
                raise ValueError(
                    f"Entrada PGC {index + 1} incompleta"
                )

            entry_id = data[0]
            flags = data[1]
            parental_mask = int.from_bytes(data[2:4], "big")
            pgc_start_byte = int.from_bytes(data[4:8], "big")

            # Los dos bits superiores representan block_mode;
            # los dos siguientes representan block_type.
            block_mode = (flags >> 6) & 0b11
            block_type = (flags >> 4) & 0b11

            if not search_table_size <= pgc_start_byte < table_size:
                raise ValueError(
                    f"Offset del PGC {index + 1} fuera de los límites "
                    "de VTS_PGCIT"
                )

            entries.append(
                DvdPgcSearchEntry(
                    number=index + 1,
                    entry_id=entry_id,
                    block_mode=block_mode,
                    block_type=block_type,
                    parental_mask=parental_mask,
                    pgc_start_byte=pgc_start_byte,
                )
            )

        return DvdPgcSearchTable(
            offset=table_offset,
            last_byte=last_byte,
            entries=tuple(entries),
        )

    def read_pgc_header(
        self,
        entry: DvdPgcSearchEntry,
    ) -> DvdPgcHeader:
        """Lee los campos principales de la cabecera de un PGC."""
        table = self.read_pgc_search_table()
        reader = BinaryReader(self.path)

        if entry not in table.entries:
            raise ValueError(
                "La entrada PGC no pertenece a esta tabla"
            )

        relative_offset = entry.pgc_start_byte
        table_size = table.last_byte + 1

        if relative_offset + self.PGC_HEADER_SIZE > table_size:
            raise ValueError(
                "La cabecera PGC excede los límites de VTS_PGCIT"
            )

        pgc_offset = table.offset + relative_offset
        data = reader.read_bytes(
            pgc_offset,
            self.PGC_HEADER_SIZE,
        )

        if len(data) != self.PGC_HEADER_SIZE:
            raise ValueError("Cabecera PGC incompleta")

        return DvdPgcHeader(
            offset=pgc_offset,
            number_programs=data[0x02],
            number_cells=data[0x03],
            playback_time_raw=data[0x04:0x08],
            command_table_offset=int.from_bytes(
                data[0xE4:0xE6], "big"
            ),
            program_map_offset=int.from_bytes(
                data[0xE6:0xE8], "big"
            ),
            cell_playback_offset=int.from_bytes(
                data[0xE8:0xEA], "big"
            ),
            cell_position_offset=int.from_bytes(
                data[0xEA:0xEC], "big"
            ),
        )

    def read_program_map(
        self,
        header: DvdPgcHeader,
    ) -> tuple[int, ...]:
        """Lee la celda inicial de cada programa del PGC."""
        if header.number_programs == 0:
            return ()

        if header.program_map_offset == 0:
            raise ValueError("El PGC no contiene mapa de programas")

        if not (
            self.PGC_HEADER_SIZE
            <= header.program_map_offset
            < self.PGC_HEADER_SIZE + 0x10000
        ):
            raise ValueError("Offset del mapa de programas no válido")

        reader = BinaryReader(self.path)
        offset = header.offset + header.program_map_offset
        data = reader.read_bytes(offset, header.number_programs)

        if len(data) != header.number_programs:
            raise ValueError("Mapa de programas incompleto")

        cell_numbers = tuple(data)

        for program_number, cell_number in enumerate(cell_numbers, 1):
            if not 1 <= cell_number <= header.number_cells:
                raise ValueError(
                    f"Celda inválida para el programa {program_number}: "
                    f"{cell_number}"
                )

        return cell_numbers

    def read_cell_playback_table(
        self,
        header: DvdPgcHeader,
    ) -> tuple[DvdCellPlaybackInfo, ...]:
        """Lee las entradas de reproducción de las celdas del PGC."""
        if header.number_cells == 0:
            return ()

        if header.cell_playback_offset == 0:
            raise ValueError(
                "El PGC no contiene tabla de reproducción de celdas"
            )

        table = self.read_pgc_search_table()

        if not any(
            entry.pgc_start_byte == header.offset - table.offset
            for entry in table.entries
        ):
            raise ValueError("El PGC no pertenece a esta tabla")

        relative_end = (
            header.cell_playback_offset
            + header.number_cells * self.CELL_PLAYBACK_ENTRY_SIZE
        )

        if relative_end > table.last_byte + 1 - (
            header.offset - table.offset
        ):
            raise ValueError(
                "La tabla de reproducción excede los límites de VTS_PGCIT"
            )

        reader = BinaryReader(self.path)
        offset = header.offset + header.cell_playback_offset
        cells = []

        for index in range(header.number_cells):
            entry_offset = (
                offset + index * self.CELL_PLAYBACK_ENTRY_SIZE
            )
            data = reader.read_bytes(
                entry_offset,
                self.CELL_PLAYBACK_ENTRY_SIZE,
            )

            if len(data) != self.CELL_PLAYBACK_ENTRY_SIZE:
                raise ValueError(
                    f"Entrada de reproducción de celda {index + 1} incompleta"
                )

            cells.append(
                DvdCellPlaybackInfo(
                    number=index + 1,
                    category_byte=data[0],
                    flags_byte=data[1],
                    still_time=data[2],
                    cell_command=data[3],
                    playback_time_raw=data[4:8],
                    first_vobu_start_sector=int.from_bytes(
                        data[8:12], "big"
                    ),
                    first_ilvu_end_sector=int.from_bytes(
                        data[12:16], "big"
                    ),
                    last_vobu_start_sector=int.from_bytes(
                        data[16:20], "big"
                    ),
                    last_vobu_end_sector=int.from_bytes(
                        data[20:24], "big"
                    ),
                )
            )

        return tuple(cells)