from pathlib import Path

from auroradvd.dvd.chapter_index import DvdChapterIndex


def make_disc(path: Path) -> None:
    video_ts = path / "VIDEO_TS"
    video_ts.mkdir()

    vmg = bytearray(4096)
    vmg[:12] = b"DVDVIDEO-VMG"
    vmg[0xC4:0xC8] = (1).to_bytes(4, "big")
    vmg[2048:2050] = (2).to_bytes(2, "big")
    vmg[2052:2056] = (31).to_bytes(4, "big")
    for offset, local_title, count in ((2056, 2, 7), (2068, 1, 4)):
        vmg[offset + 2:offset + 4] = count.to_bytes(2, "big")
        vmg[offset + 6] = 3
        vmg[offset + 7] = local_title
    (video_ts / "VIDEO_TS.IFO").write_bytes(vmg)

    vts = bytearray(4096)
    vts[:12] = b"DVDVIDEO-VTS"
    vts[0xC8:0xCC] = (1).to_bytes(4, "big")
    vts[2048:2050] = (2).to_bytes(2, "big")
    vts[2052:2056] = (27).to_bytes(4, "big")
    vts[2056:2060] = (16).to_bytes(4, "big")
    vts[2060:2064] = (20).to_bytes(4, "big")
    for offset, program in ((2064, 1), (2068, 1), (2072, 2)):
        vts[offset:offset + 2] = (1).to_bytes(2, "big")
        vts[offset + 2:offset + 4] = program.to_bytes(2, "big")
    (video_ts / "VTS_03_0.IFO").write_bytes(vts)


def test_uses_vmg_to_resolve_title_in_vts(tmp_path: Path) -> None:
    make_disc(tmp_path)
    index = DvdChapterIndex(tmp_path)

    assert index.count(1) == 2
    assert index.count(2) == 1
    assert index.count(3) is None


def test_uses_vmg_count_when_ptt_is_missing(tmp_path: Path) -> None:
    make_disc(tmp_path)
    (tmp_path / "VIDEO_TS" / "VTS_03_0.IFO").unlink()

    assert DvdChapterIndex(tmp_path).count(1) == 7


def test_missing_ifo_allows_engine_fallback(tmp_path: Path) -> None:
    assert DvdChapterIndex(tmp_path).count(1) is None
