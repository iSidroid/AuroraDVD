from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from auroradvd.player.dvd_player import DvdPlayer
from auroradvd.player.playback_status import PlaybackState, PlaybackStatus, Tracks


def fake_engine() -> Mock:
    engine = Mock()
    engine.get_state.return_value = "playing"
    engine.get_title.return_value = 1
    engine.get_chapter_count.return_value = 3
    engine.get_chapter.return_value = 0
    engine.can_pause.return_value = True

    engine.audio_get_track_description.return_value = [
        (-1, b"Disable"), (12, b"Spanish"), (13, b"English"),
    ]
    engine.audio_get_track.return_value = 12
    engine.video_get_track_description.return_value = [(3, b"Video 1")]
    engine.video_get_track.return_value = 3
    engine.video_get_spu_description.return_value = [
        (-1, b"Disable"), (22, b"Spanish"), (25, b"English"),
    ]
    engine.video_get_spu.return_value = -1
    return engine


@pytest.fixture
def player(tmp_path):
    backend = DvdPlayer()
    engine = fake_engine()
    backend._player = engine
    backend._vlc = SimpleNamespace(State=SimpleNamespace(
        Playing="playing", Paused="paused", Ended="ended", Stopped="stopped",
        Error="error",
    ))
    backend._drive = tmp_path
    backend._chapter_index = Mock()
    backend._chapter_index.count.return_value = None
    backend._playback_id = 8
    return backend, engine


def test_pause_and_resume_keep_loaded_media_and_ignore_stale_session(player):
    backend, engine = player
    backend.set_paused(7, True)
    engine.set_pause.assert_not_called()
    engine.can_pause.return_value = False
    backend.set_paused(8, True)
    engine.set_pause.assert_not_called()
    engine.can_pause.return_value = True
    backend.set_paused(8, True)
    engine.set_pause.assert_called_once_with(1)

    engine.get_state.return_value = "paused"
    backend.set_paused(8, False)
    engine.set_pause.assert_called_with(0)
    engine.set_media.assert_not_called()
    engine.stop.assert_not_called()


def test_stop_releases_media_and_prevents_late_chapter_commands(player):
    backend, engine = player
    stopped = Mock()
    backend.stopped.connect(stopped)

    backend.stop()
    backend.select_chapter(8, 1, 3)

    engine.stop.assert_called_once_with()
    engine.set_media.assert_called_once_with(None)
    engine.set_chapter.assert_not_called()
    stopped.assert_called_once_with()


def test_volume_is_bounded_and_available_before_media(player):
    backend, engine = player
    backend._player = None
    backend.set_volume(37)
    backend._player = engine
    backend._update_state()
    engine.audio_set_volume.assert_called_with(37)

    backend.set_volume(124)
    engine.audio_set_volume.assert_called_with(100)
    backend.set_volume(-5)
    engine.audio_set_volume.assert_called_with(0)


def test_navigation_is_title_scoped_and_stops_at_boundaries(player):
    backend, engine = player
    backend.step_chapter(8, 1, -1)
    engine.set_chapter.assert_not_called()

    backend.step_chapter(8, 1, 1)
    engine.set_chapter.assert_called_once_with(1)
    backend.select_chapter(8, 1, 3)
    engine.set_chapter.assert_called_with(2)

    engine.set_chapter.reset_mock()
    engine.get_chapter.return_value = 2
    backend.step_chapter(8, 1, 1)
    backend.select_chapter(8, 2, 1)
    backend.select_chapter(7, 1, 1)
    engine.get_title.return_value = 0
    backend.select_chapter(8, 0, 2)
    engine.set_chapter.assert_not_called()


def test_chapter_snapshot_respects_ifo_and_updates_without_state_change(player):
    backend, engine = player
    published = Mock()
    backend.controls_changed.connect(published)
    backend._chapter_index.count.return_value = 2
    backend._update_state()
    status = published.call_args.args[1]
    assert status.chapters == (1, 2)
    assert status.chapter == 1

    engine.get_title.return_value = 2
    engine.get_chapter.return_value = 2
    backend._chapter_index.count.return_value = None
    backend._update_state()
    status = published.call_args.args[1]
    assert status.title == 2
    assert status.chapters == (1, 2, 3)
    assert status.chapter == 3

    engine.get_title.return_value = 0
    backend._update_state()
    assert published.call_args.args[1].chapters == ()


def test_audio_video_and_subtitle_selection_uses_engine_track_ids(player):
    backend, engine = player
    engine.video_get_track_description.return_value = [(3, b"Video 1"), (5, b"Video 2")]
    backend.select_track(8, 1, "audio", 13)
    backend.select_track(8, 1, "audio", -1)
    backend.select_track(8, 2, "video", 5)
    backend.select_track(8, 1, "video", 5)
    backend.select_track(8, 1, "subtitles", 22)
    backend.select_track(8, 1, "subtitles", 25)
    backend.select_track(8, 1, "subtitles", -1)
    engine.audio_set_track.assert_called_once_with(13)
    engine.video_set_track.assert_called_once_with(5)
    assert [call.args[0] for call in engine.video_set_spu.call_args_list] == [22, 25, -1]

    published = Mock()
    backend.controls_changed.connect(published)
    backend._update_state()
    status = published.call_args.args[1]
    assert status.subtitles.active == -1
    assert status.subtitles.options[0] == (-1, "Desactivados")

    engine.get_title.return_value = 2
    engine.audio_get_track_description.return_value = [(14, "French")]
    engine.audio_get_track.return_value = 14
    engine.video_get_spu_description.return_value = []
    backend._update_state()
    status = published.call_args.args[1]
    assert status.audio == Tracks(((14, "French"),), 14)
    assert status.subtitles == Tracks()
