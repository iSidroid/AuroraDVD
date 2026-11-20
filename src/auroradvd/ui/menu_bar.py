"""
AuroraDVD
==========

Módulo:
    menu_bar

Responsabilidad:
    Contiene la barra de menús principal de la aplicación.

Autor:
    Isidro Riquelme
"""

from PySide6.QtGui import QActionGroup
from PySide6.QtWidgets import QMenuBar

from auroradvd.ui.actions import ApplicationActions


class MenuBar(QMenuBar):
    """
    Barra de menús principal de AuroraDVD.
    """

    def __init__(self, actions: ApplicationActions) -> None:
        super().__init__()

        self._actions = actions

        self._build_ui()

    def _build_ui(self) -> None:
        """
        Construye la barra de menús.
        """

        file_menu = self.addMenu("&Archivo")

        file_menu.addAction(self._actions.open_dvd)
        file_menu.addAction(self._actions.open_iso)
        file_menu.addAction(self._actions.open_ts)
        file_menu.addSeparator()
        file_menu.addAction(self._actions.exit)

        playback = self.addMenu("&Reproducción")
        for action in (self._actions.play, self._actions.pause, self._actions.resume,
                       self._actions.stop, self._actions.previous, self._actions.next):
            playback.addAction(action)
        self.chapters = playback.addMenu("Capítulos")
        video = self.addMenu("&Video")
        video.addAction(self._actions.fullscreen)
        self.video_tracks = video.addMenu("Pista de video")
        self.subtitles = video.addMenu("Subtítulos")
        audio = self.addMenu("A&udio")
        audio.addAction(self._actions.mute)
        self.audio_tracks = audio.addMenu("Pista de audio")
        tools = self.addMenu("&Herramientas")
        tools.addAction(self._actions.eject_drive)
        tools.addAction(self._actions.close_tray)
        help_menu = self.addMenu("A&yuda")
        help_menu.addAction(self._actions.help)
        help_menu.addAction(self._actions.about)

    def bind_selectors(self, controls) -> None:
        self._selector_menus = (
            (self.chapters, controls.chapter),
            (self.video_tracks, controls.video),
            (self.subtitles, controls.subtitles),
            (self.audio_tracks, controls.audio),
        )
        for menu, combo in self._selector_menus:
            menu.aboutToShow.connect(lambda menu=menu, combo=combo: self._fill(menu, combo))

    def update_selectors(self) -> None:
        for menu, combo in self._selector_menus:
            menu.setEnabled(combo.isEnabled())

    def _fill(self, menu, combo) -> None:
        menu.clear()
        group = QActionGroup(menu)
        group.setExclusive(True)
        title = combo.property("dvdTitle")
        for index in range(combo.count()):
            action = menu.addAction(combo.itemText(index))
            action.setCheckable(True)
            action.setChecked(index == combo.currentIndex())
            group.addAction(action)
            # Reuse the selector's existing path to the player.
            action.triggered.connect(
                lambda checked=False, index=index, value=combo.itemData(index):
                self._activate(combo, title, index, value)
            )
        previous = getattr(menu, "_track_group", None)
        if previous is not None:
            previous.deleteLater()
        menu._track_group = group
    def _activate(self, combo, title, index, value) -> None:
        if (
            combo.isEnabled()
            and combo.property("dvdTitle") == title
            and combo.itemData(index) == value
        ):
            combo.activated.emit(index)
