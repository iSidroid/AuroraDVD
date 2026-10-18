
"""Decodificación de los campos de tiempo DVD-Video."""

from dataclasses import dataclass
from datetime import timedelta


@dataclass(frozen=True)
class DvdTime:
    """Representa un campo de tiempo DVD-Video decodificado."""

    hours: int
    minutes: int
    seconds: int
    frames: int
    frame_rate: str
    duration: timedelta


def _decode_bcd(value: int, field_name: str) -> int:
    """Decodifica un byte BCD y rechaza dígitos inválidos."""
    high = (value >> 4) & 0x0F
    low = value & 0x0F

    if high > 9 or low > 9:
        raise ValueError(
            f"BCD inválido para {field_name}: 0x{value:02X}"
        )

    return high * 10 + low


def decode_dvd_time(raw: bytes) -> DvdTime:
    """
    Decodifica los cuatro bytes de tiempo de DVD-Video.

    El cuarto byte contiene el código de velocidad en sus dos
    bits superiores y el número BCD de fotogramas en los seis
    bits inferiores.

    Para NTSC se utiliza la convención non-drop-frame:
    30000/1001 fotogramas por segundo.
    """
    if len(raw) != 4:
        raise ValueError(
            f"El tiempo DVD debe contener 4 bytes; recibido: {len(raw)}"
        )

    hours = _decode_bcd(raw[0], "horas")
    minutes = _decode_bcd(raw[1], "minutos")
    seconds = _decode_bcd(raw[2], "segundos")

    if minutes > 59:
        raise ValueError(f"Minutos fuera de rango: {minutes}")

    if seconds > 59:
        raise ValueError(f"Segundos fuera de rango: {seconds}")

    frame_byte = raw[3]
    frame_rate_code = frame_byte >> 6
    frames_bcd = frame_byte & 0x3F

    if frame_rate_code == 0b01:
        frame_rate = "PAL"
        frames_per_second = 25
    elif frame_rate_code == 0b11:
        frame_rate = "NTSC"
        frames_per_second = 30
    else:
        raise ValueError(
            f"Código de velocidad de fotogramas reservado: "
            f"{frame_rate_code:02b}"
        )

    frames = _decode_bcd(frames_bcd, "fotogramas")

    if frames >= frames_per_second:
        raise ValueError(
            f"Número de fotogramas fuera de rango para {frame_rate}: "
            f"{frames}"
        )

    whole_seconds = hours * 3600 + minutes * 60 + seconds

    if frame_rate == "PAL":
        fractional_seconds = frames / 25
    else:
        fractional_seconds = frames * 1001 / 30000

    duration = timedelta(
        seconds=whole_seconds + fractional_seconds
    )

    return DvdTime(
        hours=hours,
        minutes=minutes,
        seconds=seconds,
        frames=frames,
        frame_rate=frame_rate,
        duration=duration,
    )