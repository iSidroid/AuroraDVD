"""
AuroraDVD
==========

Módulo:
    models

Responsabilidad:
    Define los modelos de datos utilizados para representar
    la estructura lógica de un DVD-Video.

Autor:
    Isidro Riquelme
"""

from dataclasses import dataclass, field
from datetime import timedelta
from enum import Enum
from pathlib import Path
from auroradvd.dvd.dvd_time import DvdTime, decode_dvd_time

@dataclass
class DvdChapter:
    """
    Representa un capítulo de un título DVD-Video.
    """

    number: int
    duration: timedelta | None = None


@dataclass
class DvdTitle:
    """
    Representa un título de un DVD-Video.
    """

    number: int
    vts: int
    duration: timedelta | None = None
    chapters: list[DvdChapter] = field(default_factory=list)


@dataclass
class DvdVideo:
    """
    Representa la información lógica de un DVD-Video.
    """

    drive: Path
    label: str
    titles: list[DvdTitle] = field(default_factory=list)


class IfoType(Enum):
    """Tipo de archivo IFO."""

    VMG = "VMG"
    VTS = "VTS"


@dataclass(frozen=True)
class IfoHeader:
    """Información básica de la cabecera de un archivo IFO."""

    identifier: str
    type: IfoType
    last_sector_set: int
    last_sector_ifo: int
    version: int


@dataclass(frozen=True)
class DvdTitleSearchEntry:
    """Entrada de un título en la tabla TT_SRPT."""

    number: int
    playback_type: int
    angles: int
    chapters: int
    parental_id: int
    title_set: int
    title_number_in_vts: int
    title_set_sector: int


@dataclass(frozen=True)
class DvdTitleSearchTable:
    """Tabla de búsqueda de títulos del administrador DVD."""

    offset: int
    last_byte: int
    titles: tuple[DvdTitleSearchEntry, ...]


@dataclass(frozen=True)
class DvdPartOfTitle:
    """Relaciona una parte de título con su PGC y programa."""

    pgc_number: int
    program_number: int


@dataclass(frozen=True)
class DvdTitlePartSearchEntry:
    """Partes de título pertenecientes a un título del VTS."""

    title_number: int
    parts: tuple[DvdPartOfTitle, ...]


@dataclass(frozen=True)
class DvdTitlePartSearchTable:
    """Tabla VTS_PTT_SRPT de un archivo VTS IFO."""

    offset: int
    last_byte: int
    titles: tuple[DvdTitlePartSearchEntry, ...]

@dataclass(frozen=True)
class DvdPgcSearchEntry:
    number: int
    entry_id: int
    block_mode: int
    block_type: int
    parental_mask: int
    pgc_start_byte: int


@dataclass(frozen=True)
class DvdPgcSearchTable:
    offset: int
    last_byte: int
    entries: tuple[DvdPgcSearchEntry, ...]

@dataclass(frozen=True)
class DvdPgcHeader:
    offset: int
    number_programs: int
    number_cells: int
    playback_time_raw: bytes
    command_table_offset: int
    program_map_offset: int
    cell_playback_offset: int
    cell_position_offset: int
    @property
    def playback_time(self) -> DvdTime:
        """Devuelve el tiempo de reproducción decodificado del PGC."""
        return decode_dvd_time(self.playback_time_raw)

@dataclass(frozen=True)
class DvdCellPlaybackInfo:
    number: int
    category_byte: int
    flags_byte: int
    still_time: int
    cell_command: int
    playback_time_raw: bytes
    first_vobu_start_sector: int
    first_ilvu_end_sector: int
    last_vobu_start_sector: int
    last_vobu_end_sector: int
    @property
    def playback_time(self) -> DvdTime:
        """Devuelve el tiempo de reproducción decodificado de la celda."""
        return decode_dvd_time(self.playback_time_raw)