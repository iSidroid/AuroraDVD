
from datetime import timedelta

import pytest

from auroradvd.dvd.dvd_time import decode_dvd_time


def test_decode_ntsc_time():
    result = decode_dvd_time(bytes.fromhex("00 06 48 D6"))

    assert result.hours == 0
    assert result.minutes == 6
    assert result.seconds == 48
    assert result.frames == 16
    assert result.frame_rate == "NTSC"
    assert result.duration.total_seconds() == pytest.approx(
        408 + 16 * 1001 / 30000
    )


def test_decode_pal_time():
    # 1 minuto, 2 segundos y 12 fotogramas a 25 fps.
    result = decode_dvd_time(bytes.fromhex("00 01 02 52"))

    assert result.frame_rate == "PAL"
    assert result.frames == 12
    assert result.duration.total_seconds() == pytest.approx(62.48)

@pytest.mark.parametrize(
    "raw",
    [
        bytes.fromhex("1A 00 00 C0"),  # Horas BCD inválidas
        bytes.fromhex("00 6A 00 C0"),  # Minutos BCD inválidos
        bytes.fromhex("00 00 6A C0"),  # Segundos BCD inválidos
        bytes.fromhex("00 00 00 DA"),  # Fotogramas BCD inválidos
        bytes.fromhex("00 00 00 00"),  # Código reservado
        bytes.fromhex("00 00 00 80"),  # Código reservado
        bytes.fromhex("00 00 00 5A"),  # 30 fotogramas NTSC
        bytes.fromhex("00 00 00 65"),  # 25 fotogramas PAL: fuera de rango
    ],
)
def test_decode_rejects_invalid_time(raw):
    with pytest.raises(ValueError):
        decode_dvd_time(raw)


@pytest.mark.parametrize(
    "raw",
    [
        b"",
        b"\x00\x00\x00",
        b"\x00\x00\x00\x00\x00",
    ],
)
def test_decode_requires_exactly_four_bytes(raw):
    with pytest.raises(ValueError):
        decode_dvd_time(raw)