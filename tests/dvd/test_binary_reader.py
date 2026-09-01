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

def test_read_uint8(tmp_path: Path):
    file_path = tmp_path / "test.bin"

    file_path.write_bytes(
        b"\x00\x7F\xFF"
    )

    reader = BinaryReader(file_path)

    assert reader.read_uint8(0) == 0
    assert reader.read_uint8(1) == 127
    assert reader.read_uint8(2) == 255

def test_read_bcd8(tmp_path: Path):
    file_path = tmp_path / "test.bin"

    file_path.write_bytes(
        b"\x00\x12\x25\x59"
    )

    reader = BinaryReader(file_path)

    assert reader.read_bcd8(0) == 0
    assert reader.read_bcd8(1) == 12
    assert reader.read_bcd8(2) == 25
    assert reader.read_bcd8(3) == 59

def test_read_bcd8_invalid_value(tmp_path: Path):
    file_path = tmp_path / "test.bin"

    file_path.write_bytes(
        b"\x1A"
    )

    reader = BinaryReader(file_path)

    with pytest.raises(ValueError):
        reader.read_bcd8(0)

def test_sector_to_offset():
    reader = BinaryReader(Path("dummy.bin"))

    assert reader.sector_to_offset(0) == 0
    assert reader.sector_to_offset(1) == 2048
    assert reader.sector_to_offset(13) == 26624

def test_sector_to_offset_negative():
    reader = BinaryReader(Path("dummy.bin"))

    with pytest.raises(ValueError):
        reader.sector_to_offset(-1)
