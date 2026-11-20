"""Playback information passed from the player thread to the window."""

from dataclasses import dataclass
from enum import Enum


class PlaybackState(Enum):
    IDLE = "idle"
    OPENING = "opening"
    PLAYING = "playing"
    PAUSED = "paused"
    STOPPING = "stopping"


@dataclass(frozen=True)
class Tracks:
    options: tuple[tuple[int, str], ...] = ()
    active: int | None = None


@dataclass(frozen=True)
class PlaybackStatus:
    state: PlaybackState = PlaybackState.IDLE
    can_pause: bool = False
    title: int = 0
    elapsed_ms: int | None = None
    duration_ms: int | None = None
    seekable: bool = False
    chapters: tuple[int, ...] = ()
    chapter: int | None = None
    audio: Tracks = Tracks()
    video: Tracks = Tracks()
    subtitles: Tracks = Tracks()
