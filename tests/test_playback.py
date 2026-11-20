from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from auroradvd.player.dvd_player import DvdPlayer
from auroradvd.player.playback_status import PlaybackState, PlaybackStatus, Tracks
from auroradvd.ui.main_window import MainWindow
from auroradvd.ui.widgets.playback_controls import PlaybackControls


def fake_engine() -> Mock:
    engine = Mock()
    engine.get_state.return_value = "playing"
    engine.get_title.return_value = 1
    engine.get_chapter_count.return_value = 3
    engine.get_chapter.return_value = 0
    engine.can_pause.return_value = True
    engine.get_time.return_value = 12000
    engine.is_seekable.return_value = True

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
    backend._title_durations = {1: 120000, 2: 90000}
    backend._vlc.TitleDescription = __import__("ctypes").c_int64
    backend._vlc.libvlc_media_player_get_full_title_descriptions = Mock(return_value=0)
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


@pytest.fixture
def qapp(monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    return QApplication.instance() or QApplication([])


def test_controls_render_and_emit_only_user_selection(qapp):
    controls = PlaybackControls()
    chapter = Mock()
    tracks = Mock()
    controls.chapter_requested.connect(chapter)
    controls.track_requested.connect(tracks)
    controls.show()
    assert controls.play_button.isEnabled()
    assert not controls.stop_button.isEnabled()

    controls.update_status(PlaybackStatus(
        state=PlaybackState.PLAYING,
        can_pause=True,
        title=1,
        chapters=(1, 2),
        chapter=1,
        audio=Tracks(((10, "Español"), (11, "Inglés")), 11),
        video=Tracks(((2, "Video"),), 2),
        subtitles=Tracks(((-1, "Desactivados"), (22, "Español")), 22),
    ))
    assert controls.pause_button.isEnabled()
    assert not controls.previous_button.isEnabled()
    assert controls.next_button.isEnabled()
    assert controls.audio.currentData() == 11
    assert controls.video.isHidden()
    assert controls.subtitles.currentData() == 22
    chapter.assert_not_called()
    tracks.assert_not_called()

    controls.chapter.activated.emit(1)
    controls.audio.activated.emit(0)
    controls.subtitles.activated.emit(0)
    chapter.assert_called_once_with(2)
    assert [call.args for call in tracks.call_args_list] == [("audio", 10), ("subtitles", -1)]

    controls.update_status(PlaybackStatus(
        state=PlaybackState.PAUSED,
        title=2,
        chapters=(1, 2),
        chapter=2,
        video=Tracks(((3, "Video 1"), (4, "Video 2")), 4),
    ))
    assert controls.resume_button.isEnabled()
    assert controls.previous_button.isEnabled()
    assert not controls.next_button.isEnabled()
    assert controls.video.isVisible()
    assert controls.video.currentData() == 4
    assert not controls.subtitles.isEnabled()
    assert controls.subtitles.currentText() == "Sin subtítulos"
    controls.close()


def test_fullscreen_reveals_same_controls_and_escape_restores_window(qapp, monkeypatch):
    monkeypatch.setattr(
        "auroradvd.ui.main_window.OpticalDriveService.get_optical_drives", lambda self: []
    )
    window = MainWindow()
    window.showMaximized()
    qapp.processEvents()
    window.activateWindow()
    qapp.processEvents()
    video = window._video_widget
    controls = window._controls
    handle = video.show_video()
    monkeypatch.setattr(MainWindow, "isActiveWindow", lambda self: True)

    def move_cursor(point):
        monkeypatch.setattr(
            "auroradvd.ui.widgets.video_widget.QCursor",
            SimpleNamespace(pos=lambda: video.mapToGlobal(point)),
        )
        video._update_control_visibility()

    controls.fullscreen_button.click()
    qapp.processEvents()
    assert window.isFullScreen()
    assert window.menuBar().isHidden()
    assert controls.isHidden()

    move_cursor(QPoint(video.width() // 2, video.height() - 1))
    assert controls.isVisible()
    move_cursor(controls.geometry().center())
    assert controls.isVisible()
    move_cursor(QPoint(10, 10))
    assert controls.isHidden()

    QTest.keyClick(window, Qt.Key.Key_Escape)
    qapp.processEvents()
    assert not window.isFullScreen()
    assert window.isMaximized()
    assert controls.isVisible()
    assert video.show_video() == handle
    window.close()



def test_play_reopens_available_disc_or_asks_for_a_drive(qapp, monkeypatch):
    monkeypatch.setattr(
        "auroradvd.ui.main_window.OpticalDriveService.get_optical_drives", lambda self: []
    )
    open_dvd = Mock()
    play_dvd = Mock()
    monkeypatch.setattr(MainWindow, "_open_dvd", open_dvd)
    monkeypatch.setattr(MainWindow, "_play_dvd", play_dvd)
    window = MainWindow()
    window._last_drive = Path("E:/")
    has_media = Mock(return_value=True)
    monkeypatch.setattr(window._optical_drive_service, "has_media", has_media)

    window._controls.play_button.click()
    play_dvd.assert_called_once_with(Path("E:/"))
    open_dvd.assert_not_called()

    has_media.return_value = False
    window._controls.play_button.click()
    open_dvd.assert_called_once_with()
    window.close()



def test_timeline_reports_title_duration_and_updates_while_paused(player):
    backend, engine = player
    engine.get_length.return_value = 15000  # Deliberately shorter PGC.
    status = backend._read_controls(PlaybackState.PLAYING)
    assert status.elapsed_ms == 12000
    assert status.duration_ms == 120000
    assert status.seekable

    engine.get_state.return_value = "paused"
    engine.get_time.return_value = 65000
    published = Mock()
    backend.controls_changed.connect(published)
    backend._update_state()
    status = published.call_args.args[1]
    assert status.state == PlaybackState.PAUSED
    assert status.elapsed_ms == 65000
    assert status.duration_ms == 120000

    engine.get_title.return_value = 2
    assert backend._read_controls(PlaybackState.PLAYING).duration_ms == 90000
    backend._title_durations.clear()
    assert backend._read_controls(PlaybackState.PLAYING).duration_ms is None


def test_seek_revalidates_session_title_and_capability(player):
    backend, engine = player
    backend.seek(8, 1, 45000)
    engine.set_time.assert_called_once_with(45000)
    backend.seek(8, 1, 999999)
    engine.set_time.assert_called_with(120000)
    engine.set_time.reset_mock()
    backend.seek(7, 1, 10000)
    backend.seek(8, 2, 10000)
    engine.is_seekable.return_value = False
    backend.seek(8, 1, 10000)
    engine.is_seekable.return_value = True
    backend._title_durations.clear()
    backend.seek(8, 1, 10000)
    engine.set_time.assert_not_called()


def test_mute_keeps_volume_and_is_applied_after_resume(player):
    backend, engine = player
    backend.set_muted(True)
    backend.set_volume(38)
    backend._update_state()
    engine.audio_set_mute.assert_called_with(True)
    engine.audio_set_volume.assert_called_with(38)
    backend.set_muted(False)
    engine.audio_set_mute.assert_called_with(False)


def test_progress_preview_does_not_seek_on_timer_updates(qapp):
    from dataclasses import replace
    from auroradvd.ui.widgets.playback_progress import PlaybackProgress, format_time

    assert format_time(3661000) == "01:01:01"
    assert format_time(None) == "--:--:--"
    widget = PlaybackProgress()
    seek = Mock()
    widget.seek_requested.connect(seek)
    status = PlaybackStatus(
        state=PlaybackState.PLAYING, title=1, duration_ms=120000,
        elapsed_ms=12000, seekable=True,
    )
    widget.update_status(status)
    assert widget.elapsed.text() == "00:00:12"
    assert widget.duration.text() == "00:02:00"
    seek.assert_not_called()
    widget.slider.setSliderDown(True)
    widget.slider.setValue(5000)
    widget.update_status(replace(status, elapsed_ms=14000))
    assert widget.slider.value() == 5000
    assert widget.elapsed.text() == "00:01:00"
    seek.assert_not_called()
    widget.slider.setSliderDown(False)
    seek.assert_called_once_with(60000)

    widget.slider.setSliderDown(True)
    widget.slider.setValue(7000)
    seek.reset_mock()
    widget.update_status(replace(status, title=2, elapsed_ms=0))
    seek.assert_not_called()
    assert widget.slider.value() == 0

    widget.update_status(replace(status, duration_ms=None, seekable=False))
    assert not widget.slider.isEnabled()
    assert widget.duration.text() == "--:--:--"
    widget.update_status(PlaybackStatus())
    assert widget.elapsed.text() == "00:00:00"
    widget.close()


def test_menus_actions_and_keyboard_share_commands(qapp, monkeypatch):
    from PySide6.QtWidgets import QLineEdit

    monkeypatch.setattr(
        "auroradvd.ui.main_window.OpticalDriveService.get_optical_drives", lambda self: []
    )
    window = MainWindow()
    window.show()
    window.activateWindow()
    qapp.processEvents()
    monkeypatch.setattr(MainWindow, "isActiveWindow", lambda self: True)
    names = [action.text() for action in window.menuBar().actions()]
    assert names == ["&Archivo", "&Reproducción", "&Video", "A&udio", "&Herramientas", "A&yuda"]
    assert len({name.split("&")[1][0].lower() for name in names}) == 6
    assert window._actions.open_dvd.shortcut().toString() == "Ctrl+D"

    pause = Mock()
    stop = Mock()
    chapter = Mock()
    window._pause_requested.connect(pause)
    window._stop_dvd_requested.connect(stop)
    window._chapter_step_requested.connect(chapter)
    window._playing_drive = Path("E:/")
    status = PlaybackStatus(
        state=PlaybackState.PLAYING, can_pause=True, title=1,
        chapters=(1, 2, 3), chapter=2,
    )
    window._set_playback_status(status)
    window.setFocus()
    QTest.keyClick(window, Qt.Key.Key_Space)
    pause.assert_called_once_with(0, True)
    QTest.keyClick(window, Qt.Key.Key_M)
    assert window._actions.mute.isChecked()
    QTest.keyClick(window, Qt.Key.Key_Right, Qt.KeyboardModifier.ControlModifier)
    chapter.assert_called_once_with(0, 1, 1)

    edit = QLineEdit(window)
    edit.show()
    edit.setFocus()
    qapp.processEvents()
    QTest.keyClicks(edit, "s m")
    assert edit.text() == "s m"
    stop.assert_not_called()
    assert window._actions.mute.isChecked()

    window._controls.pause_button.click()
    assert pause.call_count == 2
    window._actions.stop.trigger()
    stop.assert_called_once_with()
    assert window._playback_status.state == PlaybackState.STOPPING
    window._playback_stopped()
    assert window._actions.play.isEnabled()
    window.close()



def test_native_title_metadata_is_released_and_cached(player):
    import ctypes

    backend, engine = player

    class Title(ctypes.Structure):
        _fields_ = [("duration", ctypes.c_int64)]

    descriptions = [Title(0), Title(123456)]
    pointers = (ctypes.POINTER(Title) * 2)(*[ctypes.pointer(item) for item in descriptions])

    def read(player, output):
        ctypes.cast(
            output, ctypes.POINTER(ctypes.POINTER(Title))
        )[0] = ctypes.cast(pointers, ctypes.POINTER(Title))
        return 2

    backend._title_durations.clear()
    backend._vlc.TitleDescription = Title
    backend._vlc.libvlc_media_player_get_full_title_descriptions = Mock(side_effect=read)
    backend._vlc.libvlc_title_descriptions_release = Mock()
    assert backend._title_duration(1) == 123456
    assert backend._title_duration(1) == 123456
    backend._vlc.libvlc_media_player_get_full_title_descriptions.assert_called_once()
    backend._vlc.libvlc_title_descriptions_release.assert_called_once()
    released = backend._vlc.libvlc_title_descriptions_release.call_args.args[0]
    assert isinstance(released, ctypes.POINTER(ctypes.POINTER(Title)))
    assert released[1].contents.duration == 123456



def test_dynamic_menu_tracks_use_existing_selector_and_reject_old_title(qapp, monkeypatch):
    from dataclasses import replace

    monkeypatch.setattr(
        "auroradvd.ui.main_window.OpticalDriveService.get_optical_drives", lambda self: []
    )
    window = MainWindow()
    selected = Mock()
    window._track_requested.connect(selected)
    status = PlaybackStatus(
        state=PlaybackState.PLAYING, title=1,
        audio=Tracks(((12, "Español"), (13, "Inglés")), 12),
    )
    window._set_playback_status(status)
    menu = window.menuBar().audio_tracks
    window.menuBar()._fill(menu, window._controls.audio)
    assert menu.actions()[0].isChecked()
    menu.actions()[1].trigger()
    selected.assert_called_once_with(0, 1, "audio", 13)
    selected.reset_mock()
    window._set_playback_status(replace(status, title=2))
    menu.actions()[1].trigger()
    selected.assert_not_called()
    window.close()


@pytest.mark.parametrize("ending", ["ended", "error"])
def test_terminal_states_clear_timeline_and_release_media(player, ending):
    backend, engine = player
    engine.get_state.return_value = ending
    finished = Mock()
    backend.finished.connect(finished)
    backend._update_state()
    assert backend._drive is None
    assert not backend._timer.isActive()
    engine.set_media.assert_called_once_with(None)
    finished.assert_called_once()
