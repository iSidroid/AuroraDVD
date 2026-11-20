import ctypes
import os
import sys
from pathlib import Path

from PySide6.QtCore import QObject, QTimer, Signal, Slot

from auroradvd.dvd.chapter_index import DvdChapterIndex
from auroradvd.player.playback_status import PlaybackState, PlaybackStatus, Tracks


_TRACK_METHODS = {
    "audio": ("audio_get_track_description", "audio_get_track", "audio_set_track"),
    "video": ("video_get_track_description", "video_get_track", "video_set_track"),
    "subtitles": ("video_get_spu_description", "video_get_spu", "video_set_spu"),
}


class DvdPlaybackError(RuntimeError):
    pass


class DvdPlayer(QObject):
    playing = Signal(int, str)
    finished = Signal(int, str)
    stopped = Signal()
    closed = Signal()
    controls_changed = Signal(int, object)

    def __init__(self, volume: int = 100) -> None:
        super().__init__()
        self._instance = None
        self._dll_directory = None
        self._player = None
        self._drive: Path | None = None
        self._chapter_index: DvdChapterIndex | None = None
        self._controls: PlaybackStatus | None = None
        self._volume = volume
        self._muted = False
        self._title_durations: dict[int, int] = {}
        self._playback_id = 0
        self._last_state = None

        self._timer = QTimer(self)
        self._timer.setInterval(250)
        self._timer.timeout.connect(self._update_state)

    def _configure_bundled_vlc(self) -> None:
        engine = Path(sys.executable).resolve().parent / "LibVLC"
        library = engine / "libvlc.dll"
        core = engine / "libvlccore.dll"
        plugins = engine / "plugins"
        if not (library.is_file() and core.is_file() and plugins.is_dir()):
            raise DvdPlaybackError(
                "Faltan componentes de LibVLC. Vuelve a extraer el ZIP completo."
            )
        if self._dll_directory is None:
            self._dll_directory = os.add_dll_directory(str(engine))

        os.environ["PYTHON_VLC_LIB_PATH"] = str(library)
        os.environ["PYTHON_VLC_MODULE_PATH"] = str(plugins)
        os.environ["VLC_PLUGIN_PATH"] = str(plugins)

    def _initialize_vlc(self) -> None:
        bundled = getattr(sys, "frozen", False)
        try:
            if bundled:
                self._configure_bundled_vlc()

            import vlc

            instance = vlc.Instance("--ignore-config")
        except (ImportError, OSError, NameError, SystemExit) as error:
            if bundled:
                raise DvdPlaybackError(
                    "No se pudo cargar el LibVLC incluido. "
                    "Vuelve a extraer el ZIP completo."
                ) from error
            raise DvdPlaybackError(
                "No se pudo cargar VLC. Comprueba que VLC esté instalado y que "
                "su arquitectura coincida con la de AuroraDVD."
            ) from error

        if instance is None:
            raise DvdPlaybackError("No se pudo iniciar el motor de VLC.")

        player = instance.media_player_new()
        if player is None:
            instance.release()
            raise DvdPlaybackError("No se pudo crear el reproductor de VLC.")

        self._vlc = vlc
        self._instance = instance
        self._player = player

    @Slot(int, object, object)
    def play(self, playback_id: int, drive: Path, window_handle: int) -> None:
        self._stop()
        self._playback_id = playback_id
        try:
            if self._player is None:
                self._initialize_vlc()

            media = self._instance.media_new_location(f"dvd:///{drive.as_posix()}")
            if media is None:
                raise DvdPlaybackError(f"No se pudo abrir el DVD en {drive}.")

            self._player.set_hwnd(window_handle)
            self._player.set_media(media)
            media.release()

            self._drive = drive
            self._chapter_index = DvdChapterIndex(drive)
            self._player.audio_set_volume(self._volume)
            self._player.audio_set_mute(self._muted)
            self._player.video_set_key_input(False)
            if self._player.play() == -1:
                self._stop()
                raise DvdPlaybackError(f"No se pudo reproducir el DVD en {drive}.")
        except DvdPlaybackError as error:
            self.finished.emit(playback_id, str(error))
            return

        self._timer.start()

    def _stop(self) -> None:
        self._timer.stop()
        if self._drive is not None:
            self._player.stop()
            self._player.set_media(None)
            self._drive = None
        self._last_state = None
        self._chapter_index = None
        self._title_durations.clear()
        self._controls = None

    @Slot()
    def stop(self) -> None:
        self._stop()
        self.stopped.emit()

    @Slot()
    def close(self) -> None:
        self._stop()
        if self._player is not None:
            self._player.release()
            self._instance.release()
        if self._dll_directory is not None:
            self._dll_directory.close()
        self.closed.emit()

    @Slot(int, bool)
    def set_paused(self, playback_id: int, paused: bool) -> None:
        if not self._has_playback(playback_id):
            return
        state = self._player.get_state()
        if paused and state == self._vlc.State.Playing and self._player.can_pause():
            self._player.set_pause(1)
        elif not paused and state == self._vlc.State.Paused:
            self._player.set_pause(0)

    @Slot(int)
    def set_volume(self, volume: int) -> None:
        self._volume = max(0, min(volume, 100))
        if self._player is not None:
            self._player.audio_set_volume(self._volume)

    @Slot(bool)
    def set_muted(self, muted: bool) -> None:
        self._muted = muted
        if self._player is not None:
            self._player.audio_set_mute(muted)

    def _title_duration(self, title: int) -> int | None:
        # DVD get_length() can describe the current PGC. Title descriptions
        # report the full title, including titles that span several PGCs.
        if title in self._title_durations:
            return self._title_durations[title]
        descriptions = ctypes.POINTER(self._vlc.TitleDescription)()
        count = self._vlc.libvlc_media_player_get_full_title_descriptions(
            self._player, ctypes.byref(descriptions)
        )
        if count <= 0:
            return None
        try:
            pointers = ctypes.cast(
                descriptions, ctypes.POINTER(ctypes.POINTER(self._vlc.TitleDescription))
            )
            self._title_durations = {
                index: pointers[index].contents.duration
                for index in range(count)
                if pointers[index].contents.duration > 0
            }
        finally:
            self._vlc.libvlc_title_descriptions_release(pointers, count)
        return self._title_durations.get(title)

    @Slot(int, int, object)
    def seek(self, playback_id: int, title: int, milliseconds: int) -> None:
        if not self._has_title(playback_id, title) or not self._player.is_seekable():
            return
        duration = self._title_duration(title)
        if duration is not None:
            self._player.set_time(max(0, min(milliseconds, duration)))
            self._controls = None

    @Slot(int, int, int)
    def select_chapter(self, playback_id: int, title: int, chapter: int) -> None:
        if not self._has_title(playback_id, title):
            return
        if chapter in self._chapter_numbers(title):
            self._player.set_chapter(chapter - 1)
        self._controls = None

    @Slot(int, int, int)
    def step_chapter(self, playback_id: int, title: int, direction: int) -> None:
        if direction not in (-1, 1) or not self._has_title(playback_id, title):
            return
        chapter = self._player.get_chapter()
        if chapter >= 0:
            self.select_chapter(playback_id, title, chapter + 1 + direction)

    @Slot(int, int, str, int)
    def select_track(self, playback_id: int, title: int, kind: str, track: int) -> None:
        if kind not in _TRACK_METHODS or not self._has_title(playback_id, title):
            return
        tracks = self._read_tracks(kind)
        if any(track_id == track for track_id, _ in tracks.options):
            _, _, setter = _TRACK_METHODS[kind]
            getattr(self._player, setter)(track)
        self._controls = None

    def _has_playback(self, playback_id: int) -> bool:
        return self._drive is not None and self._playback_id == playback_id

    def _has_title(self, playback_id: int, title: int) -> bool:
        return (
            self._has_playback(playback_id)
            and title > 0
            and self._player.get_title() == title
        )

    def _chapter_numbers(self, title: int) -> tuple[int, ...]:
        available = self._player.get_chapter_count()
        if available <= 0:
            return ()
        ifo_count = self._chapter_index.count(title)
        count = min(available, ifo_count) if ifo_count else available
        return tuple(range(1, count + 1))

    def _read_tracks(self, kind: str) -> Tracks:
        describe, current, _ = _TRACK_METHODS[kind]
        options = []
        for track_id, name in getattr(self._player, describe)() or ():
            if track_id < 0:
                continue
            if isinstance(name, bytes):
                name = name.decode("utf-8", errors="replace")
            options.append((track_id, name or f"Pista {len(options) + 1}"))

        active = getattr(self._player, current)()
        if kind == "subtitles" and options:
            options.insert(0, (-1, "Desactivados"))
        if not any(track_id == active for track_id, _ in options):
            active = None
        return Tracks(tuple(options), active)

    def _read_controls(self, state: PlaybackState) -> PlaybackStatus:
        title = self._player.get_title()
        can_pause = bool(self._player.can_pause())
        if title <= 0:
            # In dvdnav, title zero contains menu commands in place of chapters.
            return PlaybackStatus(state=state, can_pause=can_pause)

        chapters = self._chapter_numbers(title)
        current = self._player.get_chapter() + 1
        duration = self._title_duration(title)
        position = self._player.get_time()
        elapsed = max(0, position) if position >= 0 else None
        if elapsed is not None and duration is not None:
            elapsed = min(elapsed, duration)
        return PlaybackStatus(
            state=state,
            can_pause=can_pause,
            title=title,
            elapsed_ms=elapsed,
            duration_ms=duration,
            seekable=duration is not None and bool(self._player.is_seekable()),
            chapters=chapters,
            chapter=current if current in chapters else None,
            audio=self._read_tracks("audio"),
            video=self._read_tracks("video"),
            subtitles=self._read_tracks("subtitles"),
        )

    @Slot()
    def _update_state(self) -> None:
        state = self._player.get_state()
        changed = state != self._last_state
        self._last_state = state

        if state == self._vlc.State.Error:
            message = f"No se pudo reproducir el DVD en {self._drive}."
            self._stop()
            self.finished.emit(self._playback_id, message)
            return
        if state in (self._vlc.State.Ended, self._vlc.State.Stopped):
            self._stop()
            self.finished.emit(self._playback_id, "Reproducción finalizada.")
            return

        if state == self._vlc.State.Playing:
            if changed:
                self._player.audio_set_volume(self._volume)
                self._player.audio_set_mute(self._muted)
                self.playing.emit(self._playback_id, f"Reproduciendo DVD en {self._drive}")
            status = self._read_controls(PlaybackState.PLAYING)
        elif state == self._vlc.State.Paused:
            status = self._read_controls(PlaybackState.PAUSED)
        else:
            return

        if status != self._controls:
            self._controls = status
            self.controls_changed.emit(self._playback_id, status)
