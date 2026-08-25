"""
Pruebas para los modelos DVD-Video.
"""

from datetime import timedelta
from pathlib import Path

from auroradvd.dvd.models import DvdChapter, DvdTitle, DvdVideo
from auroradvd.dvd.models import IfoHeader, IfoType


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
        last_sector=1234,
        version=2,
    )

    assert header.identifier == "DVDVIDEO-VMG"
    assert header.type is IfoType.VMG
    assert header.last_sector == 1234
    assert header.version == 2


def test_vts_ifo_header():
    header = IfoHeader(
        identifier="DVDVIDEO-VTS",
        type=IfoType.VTS,
        last_sector=5678,
        version=1,
    )

    assert header.identifier == "DVDVIDEO-VTS"
    assert header.type is IfoType.VTS
    assert header.last_sector == 5678
    assert header.version == 1    