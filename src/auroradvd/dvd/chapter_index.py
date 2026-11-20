"""Chapter numbers for the currently open DVD-Video."""

from pathlib import Path

from auroradvd.dvd.ifo_parser import IfoParser
from auroradvd.dvd.models import DvdTitlePartSearchTable, DvdTitleSearchEntry


class DvdChapterIndex:
    def __init__(self, drive: Path) -> None:
        self._video_ts = drive / "VIDEO_TS"
        self._titles: dict[int, DvdTitleSearchEntry] | None = None
        self._title_sets: dict[int, DvdTitlePartSearchTable | None] = {}

    def count(self, title_number: int) -> int | None:
        if self._titles is None:
            try:
                titles = IfoParser(
                    self._video_ts / "VIDEO_TS.IFO"
                ).read_title_search_table().titles
            except (OSError, ValueError):
                titles = ()
            self._titles = {title.number: title for title in titles}

        title = self._titles.get(title_number)
        if title is None:
            return None

        title_set = title.title_set
        if title_set not in self._title_sets:
            try:
                table = IfoParser(
                    self._video_ts / f"VTS_{title_set:02d}_0.IFO"
                ).read_part_of_title_search_table()
            except (OSError, ValueError):
                table = None
            self._title_sets[title_set] = table

        table = self._title_sets[title_set]
        if table is not None:
            for entry in table.titles:
                if entry.title_number == title.title_number_in_vts and entry.parts:
                    return len(entry.parts)
        return title.chapters or None
