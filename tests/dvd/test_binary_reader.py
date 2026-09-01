"""
Pruebas para BinaryReader.
"""

from pathlib import Path

import pytest

from auroradvd.dvd.binary_reader import BinaryReader


def test_read_bytes(tmp_path: Path):
    file_path = tmp_path / "test.bin"

    file_path.write_bytes(
        b"\x00\x01\x02\x03\x04\x05"
    )

    reader = BinaryReader(file_path)

    result = reader.read_bytes(0x02, 3)

    assert result == b"\x02\x03\x04"


def test_read_bytes_from_start(tmp_path: Path):
    file_path = tmp_path / "test.bin"

    file_path.write_bytes(
        b"\xAA\xBB\xCC"
    )

    reader = BinaryReader(file_path)

    result = reader.read_bytes(0, 2)

    assert result == b"\xAA\xBB"


def test_negative_offset():
    reader = BinaryReader(Path("dummy.bin"))

    with pytest.raises(ValueError):
        reader.read_bytes(-1, 2)


def test_negative_size():
    reader = BinaryReader(Path("dummy.bin"))

    with pytest.raises(ValueError):
        reader.read_bytes(0, -1)

def test_read_uint32_be(tmp_path: Path):
    file_path = tmp_path / "test.bin"

    file_path.write_bytes(
        b"\x00\x01\x86\xA0"
    )

    reader = BinaryReader(file_path)

    result = reader.read_uint32_be(0)

    assert result == 100_000

def test_read_uint16_be(tmp_path: Path):
    file_path = tmp_path / "test.bin"

    file_path.write_bytes(
        b"\x00\x11"
    )

    reader = BinaryReader(file_path)

    result = reader.read_uint16_be(0)

    assert result == 0x0011
    assert result == 17

def test_read_uint32_be_insufficient_data(tmp_path: Path):
    file_path = tmp_path / "test.bin"

    file_path.write_bytes(
        b"\x00\x01"
    )

    reader = BinaryReader(file_path)

    with pytest.raises(ValueError):
        reader.read_uint32_be(0)       