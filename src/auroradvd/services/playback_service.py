"""
AuroraDVD
==========

Módulo:
    playback_service

Responsabilidad:
    Proporciona las operaciones básicas de reproducción mediante VLC.

Autor:
    Isidro Riquelme
"""

from pathlib import Path

import vlc


class PlaybackService:
    """
    Servicio encargado de controlar la reproducción mediante VLC.
    """

    def __init__(self) -> None:
        self._instance = vlc.Instance()
        self._player = self._instance.media_player_new()

    def play(self, source: Path) -> None:
        """
        Reproduce un archivo o medio indicado.

        Args:
            source: Ruta al medio que se desea reproducir.
        """

        media = self._instance.media_new(str(source))
        self._player.set_media(media)
        self._player.play()

    def pause(self) -> None:
        """
        Pausa la reproducción actual.
        """

        self._player.pause()

    def stop(self) -> None:
        """
        Detiene la reproducción actual.
        """

        self._player.stop()

    def is_playing(self) -> bool:
        """
        Indica si existe una reproducción activa.

        Returns:
            True si VLC está reproduciendo.
            False en caso contrario.
        """

        return bool(self._player.is_playing())