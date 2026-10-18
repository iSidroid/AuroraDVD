"""
Pruebas para los modelos DVD-Video.
"""

import pytest

from auroradvd.dvd.models import (
    DvdChapter,
    DvdTitle,
    DvdVideo,
    DvdPgcHeader,
    DvdCellPlaybackInfo,
    IfoHeader,
    IfoType,
)
from datetime import timedelta
from pathlib import Path


def test_dvd_chapter_creation():
    chapter = DvdChapter(
        number=1,
        duration=timedelta(minutes=5),
    )

    assert chapter.number == 1
    assert chapter.duration == timedelta(minutes=5)


def test_dvd_title_creation():
    chapter = DvdChapter(number=1)

    title = DvdTitle(
        number=1,
        vts=1,
        chapters=[chapter],
    )

    assert title.number == 1
    assert title.vts == 1
    assert len(title.chapters) == 1
    assert title.chapters[0] is chapter


def test_dvd_video_creation():
    title = DvdTitle(number=1, vts=1)

    dvd = DvdVideo(
        drive=Path("E:\\"),
        label="TEST_DVD",
        titles=[title],
    )

    assert dvd.drive == Path("E:\\")
    assert dvd.label == "TEST_DVD"
    assert len(dvd.titles) == 1
    assert dvd.titles[0] is title


def test_ifo_type_values():
    assert IfoType.VMG.value == "VMG"
    assert IfoType.VTS.value == "VTS"


def test_vmg_ifo_header():
    header = IfoHeader(
        identifier="DVDVIDEO-VMG",
        type=IfoType.VMG,
        last_sector_set=1234,
        last_sector_ifo=567,
        version=2,
    )

    assert header.identifier == "DVDVIDEO-VMG"
    assert header.type is IfoType.VMG
    assert header.last_sector_set == 1234
    assert header.last_sector_ifo == 567
    assert header.version == 2


def test_vts_ifo_header():
    header = IfoHeader(
        identifier="DVDVIDEO-VTS",
        type=IfoType.VTS,
        last_sector_set=5678,
        last_sector_ifo=123,
        version=1,
    )

    assert header.identifier == "DVDVIDEO-VTS"
    assert header.type is IfoType.VTS
    assert header.last_sector_set == 5678
    assert header.last_sector_ifo == 123
    assert header.version == 1


def test_pgc_header_playback_time():
    header = DvdPgcHeader(
        offset=0x1010,
        number_programs=1,
        number_cells=13,
        playback_time_raw=bytes.fromhex("00 06 48 D6"),
        command_table_offset=0,
        program_map_offset=0xF0,
        cell_playback_offset=0x112,
        cell_position_offset=0x24A,
    )

    result = header.playback_time

    assert result.hours == 0
    assert result.minutes == 6
    assert result.seconds == 48
    assert result.frames == 16
    assert result.frame_rate == "NTSC"
    assert header.playback_time_raw == bytes.fromhex("00 06 48 D6")


def test_cell_playback_info_time():
    raw_time = bytes.fromhex("00 06 48 D6")

    cell = DvdCellPlaybackInfo(
        number=1,
        category_byte=0x02,
        flags_byte=0,
        still_time=0,
        cell_command=0,
        playback_time_raw=raw_time,
        first_vobu_start_sector=0,
        first_ilvu_end_sector=0,
        last_vobu_start_sector=198374,
        last_vobu_end_sector=198374,
    )

    result = cell.playback_time

    assert result.duration.total_seconds() == pytest.approx(
        408 + 16 * 1001 / 30000
    )
    assert result.frame_rate == "NTSC"
    assert cell.playback_time_raw == raw_time


def test_invalid_pgc_time_preserves_raw_bytes():
    raw_time = bytes.fromhex("00 00 00 00")

    header = DvdPgcHeader(
        offset=0x1010,
        number_programs=1,
        number_cells=1,
        playback_time_raw=raw_time,
        command_table_offset=0,
        program_map_offset=0xF0,
        cell_playback_offset=0x112,
        cell_position_offset=0x24A,
    )

    assert header.playback_time_raw == raw_time

    with pytest.raises(ValueError):
        _ = header.playback_time