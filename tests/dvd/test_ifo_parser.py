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