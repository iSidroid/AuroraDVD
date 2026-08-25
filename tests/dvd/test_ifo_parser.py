"""
Pruebas para el parser inicial de archivos IFO.
"""

from pathlib import Path

from auroradvd.dvd.ifo_parser import IfoParser
from auroradvd.dvd.models import IfoType


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