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