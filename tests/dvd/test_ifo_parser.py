"""
Pruebas para el parser inicial de archivos IFO.
"""

from pathlib import Path
from auroradvd.dvd.ifo_parser import IfoParser
from auroradvd.dvd.models import IfoType
import pytest


def test_valid_vts_ifo_header(tmp_path: Path):
    ifo_path = tmp_path / "VTS_01_0.IFO"

    ifo_path.write_bytes(b"DVDVIDEO-VTS")

    parser = IfoParser(ifo_path)

    assert parser.is_valid()
    assert parser.get_type() is IfoType.VTS


def test_valid_vmg_ifo_header(tmp_path: Path):
    ifo_path = tmp_path / "VIDEO_TS.IFO"

    ifo_path.write_bytes(b"DVDVIDEO-VMG")

    parser = IfoParser(ifo_path)

    assert parser.is_valid()
    assert parser.get_type() is IfoType.VMG


def test_invalid_ifo_header(tmp_path: Path):
    ifo_path = tmp_path / "VIDEO_TS.IFO"

    ifo_path.write_bytes(b"INVALID-IFO!")

    parser = IfoParser(ifo_path)

    assert not parser.is_valid()
    assert parser.get_type() is None


def test_missing_ifo_file(tmp_path: Path):
    ifo_path = tmp_path / "VIDEO_TS.IFO"

    parser = IfoParser(ifo_path)

    assert not parser.is_valid()
    assert parser.get_type() is None


def test_parse_vts_header(tmp_path: Path):
    ifo_path = tmp_path / "VTS_01_0.IFO"

    data = bytearray(0x22)

    data[0:12] = b"DVDVIDEO-VTS"

    # Last sector of VTS set
    data[0x0C:0x10] = (100_000).to_bytes(4, "big")

    # Last sector of IFO
    data[0x1C:0x20] = (15).to_bytes(4, "big")

    # Version 1.1
    data[0x20:0x22] = (0x0011).to_bytes(2, "big")

    ifo_path.write_bytes(data)

    parser = IfoParser(ifo_path)

    header = parser.parse_header()

    assert header.identifier == "DVDVIDEO-VTS"
    assert header.type is IfoType.VTS
    assert header.last_sector_set == 100_000
    assert header.last_sector_ifo == 15
    assert header.version == 0x0011


def test_parse_vts_header_uses_binary_fields(tmp_path: Path):
    ifo_path = tmp_path / "VTS_01_0.IFO"

    data = bytearray(0x22)

    data[0:12] = b"DVDVIDEO-VTS"

    # Last sector of VTS set
    data[0x0C:0x10] = (100_000).to_bytes(4, "big")

    # Last sector of IFO
    data[0x1C:0x20] = (15).to_bytes(4, "big")

    # Version 1.1
    data[0x20:0x22] = (0x0011).to_bytes(2, "big")

    ifo_path.write_bytes(data)

    parser = IfoParser(ifo_path)

    header = parser.parse_header()

    assert header.last_sector_set == 100_000
    assert header.last_sector_ifo == 15
    assert header.version == 0x0011


def test_parse_header_rejects_truncated_ifo(tmp_path: Path):
    ifo_path = tmp_path / "VTS_01_0.IFO"

    ifo_path.write_bytes(
        b"DVDVIDEO-VTS"
    )

    parser = IfoParser(ifo_path)

    with pytest.raises(ValueError):
        parser.parse_header()


def test_read_program_map_rejects_offset_outside_file(tmp_path):
    from auroradvd.dvd.ifo_parser import IfoParser
    from auroradvd.dvd.models import DvdPgcHeader

    ifo_path = tmp_path / "synthetic.ifo"
    ifo_path.write_bytes(b"\x00" * 512)

    parser = IfoParser(ifo_path)
    header = DvdPgcHeader(
        offset=0,
        number_programs=2,
        number_cells=2,
        playback_time_raw=b"\x00" * 4,
        command_table_offset=0,
        program_map_offset=0x200,
        cell_playback_offset=0,
        cell_position_offset=0,
    )

    import pytest

    with pytest.raises(ValueError):
        parser.read_program_map(header)


def test_read_program_map_rejects_data_outside_pgcit(tmp_path, monkeypatch):
    from auroradvd.dvd.models import (
        DvdPgcHeader,
        DvdPgcSearchEntry,
        DvdPgcSearchTable,
    )

    ifo_path = tmp_path / "synthetic.ifo"
    data = bytearray(1024)

    # Los bytes del mapa existen en el archivo, pero fuera de VTS_PGCIT.
    data[0x200:0x202] = bytes([1, 2])
    ifo_path.write_bytes(data)

    parser = IfoParser(ifo_path)

    table = DvdPgcSearchTable(
        offset=0x100,
        last_byte=0xFF,
        entries=(
            DvdPgcSearchEntry(
                number=1,
                entry_id=1,
                block_mode=0,
                block_type=0,
                parental_mask=0,
                pgc_start_byte=0x10,
            ),
        ),
    )

    monkeypatch.setattr(parser, "read_pgc_search_table", lambda: table)

    header = DvdPgcHeader(
        offset=0x110,
        number_programs=2,
        number_cells=2,
        playback_time_raw=b"\x00" * 4,
        command_table_offset=0,
        program_map_offset=0xF0,
        cell_playback_offset=0,
        cell_position_offset=0,
    )

    with pytest.raises(ValueError):
        parser.read_program_map(header)


def test_read_part_of_title_search_table(tmp_path: Path):
    ifo_path = tmp_path / "VTS_01_0.IFO"
    data = bytearray(0x1000)

    # Cabecera VTS válida y puntero a VTS_PTT_SRPT, sector 1.
    data[0:12] = b"DVDVIDEO-VTS"
    data[0xC8:0xCC] = (1).to_bytes(4, "big")

    # VTS_PTT_SRPT: un título, tabla de offsets y dos partes.
    table_offset = 0x800
    data[table_offset:table_offset + 8] = (
        (1).to_bytes(2, "big")       # Número de títulos
        + (0).to_bytes(2, "big")     # Reservado
        + (19).to_bytes(4, "big")    # Último byte: offset 19
    )

    # Offset relativo al comienzo de la tabla: byte 12.
    data[table_offset + 8:table_offset + 12] = (
        12
    ).to_bytes(4, "big")

    # Dos entradas PTT: PGC 1, programas 1 y 2.
    data[table_offset + 12:table_offset + 16] = (
        (1).to_bytes(2, "big") + (1).to_bytes(2, "big")
    )
    data[table_offset + 16:table_offset + 20] = (
        (1).to_bytes(2, "big") + (2).to_bytes(2, "big")
    )

    ifo_path.write_bytes(data)
    parser = IfoParser(ifo_path)

    result = parser.read_part_of_title_search_table()

    assert result.offset == table_offset
    assert result.last_byte == 19
    assert len(result.titles) == 1
    assert result.titles[0].title_number == 1
    assert len(result.titles[0].parts) == 2
    assert result.titles[0].parts[0].pgc_number == 1
    assert result.titles[0].parts[0].program_number == 1
    assert result.titles[0].parts[1].pgc_number == 1
    assert result.titles[0].parts[1].program_number == 2


def test_read_part_of_title_search_table_rejects_zero_pointer(
    tmp_path: Path,
):
    ifo_path = tmp_path / "VTS_01_0.IFO"
    data = bytearray(0x100)

    data[0:12] = b"DVDVIDEO-VTS"
    data[0xC8:0xCC] = (0).to_bytes(4, "big")

    ifo_path.write_bytes(data)
    parser = IfoParser(ifo_path)

    with pytest.raises(ValueError, match="puntero VTS_PTT_SRPT es cero"):
        parser.read_part_of_title_search_table()


def test_read_part_of_title_search_table_rejects_truncated_header(
    tmp_path: Path,
):
    ifo_path = tmp_path / "VTS_01_0.IFO"
    data = bytearray(0x1000)

    data[0:12] = b"DVDVIDEO-VTS"

    # Sector 1: solo quedan 4 bytes antes del final del archivo.
    data[0xC8:0xCC] = (1).to_bytes(4, "big")

    ifo_path.write_bytes(data[:0x804])
    parser = IfoParser(ifo_path)

    with pytest.raises(ValueError, match="Cabecera VTS_PTT_SRPT incompleta"):
        parser.read_part_of_title_search_table()


def test_read_part_of_title_search_table_rejects_offset_inside_pointer_table(
    tmp_path: Path,
):
    ifo_path = tmp_path / "VTS_01_0.IFO"
    data = bytearray(0x1000)

    data[0:12] = b"DVDVIDEO-VTS"
    data[0xC8:0xCC] = (1).to_bytes(4, "big")

    table_offset = 0x800

    # Cabecera: un título, último byte relativo = 15.
    data[table_offset:table_offset + 8] = (
        (1).to_bytes(2, "big")
        + (0).to_bytes(2, "big")
        + (15).to_bytes(4, "big")
    )

    # Offset relativo 8: apunta al inicio de la propia tabla
    # de punteros, no al área de entradas PTT.
    data[table_offset + 8:table_offset + 12] = (
        8
    ).to_bytes(4, "big")

    ifo_path.write_bytes(data)
    parser = IfoParser(ifo_path)

    with pytest.raises(ValueError, match="Offset inválido para el título"):
        parser.read_part_of_title_search_table()


def test_read_part_of_title_search_table_rejects_truncated_table(
    tmp_path: Path,
):
    ifo_path = tmp_path / "VTS_01_0.IFO"
    data = bytearray(0x1000)

    data[0:12] = b"DVDVIDEO-VTS"
    data[0xC8:0xCC] = (1).to_bytes(4, "big")

    table_offset = 0x800

    # Cabecera: un título, pero la tabla declara 256 bytes.
    data[table_offset:table_offset + 8] = (
        (1).to_bytes(2, "big")
        + (0).to_bytes(2, "big")
        + (255).to_bytes(4, "big")
    )

    ifo_path.write_bytes(data[:0x810])
    parser = IfoParser(ifo_path)

    with pytest.raises(
        ValueError,
        match="VTS_PTT_SRPT excede los datos disponibles",
    ):
        parser.read_part_of_title_search_table()


def test_read_part_of_title_search_table_rejects_zero_pgc(
    tmp_path: Path,
):
    ifo_path = tmp_path / "VTS_01_0.IFO"
    data = bytearray(0x1000)

    data[0:12] = b"DVDVIDEO-VTS"
    data[0xC8:0xCC] = (1).to_bytes(4, "big")

    table_offset = 0x800

    # Un título, una entrada PTT de cuatro bytes.
    data[table_offset:table_offset + 8] = (
        (1).to_bytes(2, "big")
        + (0).to_bytes(2, "big")
        + (15).to_bytes(4, "big")
    )

    # Offset relativo 12: después de la cabecera y el puntero.
    data[table_offset + 8:table_offset + 12] = (
        12
    ).to_bytes(4, "big")

    # PGC = 0 (inválido), programa = 1.
    data[table_offset + 12:table_offset + 16] = (
        (0).to_bytes(2, "big")
        + (1).to_bytes(2, "big")
    )

    ifo_path.write_bytes(data)
    parser = IfoParser(ifo_path)

    with pytest.raises(
        ValueError,
        match="Referencia PGC/programa inválida",
    ):
        parser.read_part_of_title_search_table()


def test_read_part_of_title_search_table_rejects_zero_program(
    tmp_path: Path,
):
    ifo_path = tmp_path / "VTS_01_0.IFO"
    data = bytearray(0x1000)

    data[0:12] = b"DVDVIDEO-VTS"
    data[0xC8:0xCC] = (1).to_bytes(4, "big")

    table_offset = 0x800

    data[table_offset:table_offset + 8] = (
        (1).to_bytes(2, "big")
        + (0).to_bytes(2, "big")
        + (15).to_bytes(4, "big")
    )

    data[table_offset + 8:table_offset + 12] = (
        12
    ).to_bytes(4, "big")

    # PGC = 1 (válido), programa = 0 (inválido).
    data[table_offset + 12:table_offset + 16] = (
        (1).to_bytes(2, "big")
        + (0).to_bytes(2, "big")
    )

    ifo_path.write_bytes(data)
    parser = IfoParser(ifo_path)

    with pytest.raises(
        ValueError,
        match="Referencia PGC/programa inválida",
    ):
        parser.read_part_of_title_search_table()