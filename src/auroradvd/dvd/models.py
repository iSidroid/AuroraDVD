"""
AuroraDVD
==========

Módulo:
    models

Responsabilidad:
    Define los modelos de datos utilizados para representar
    la estructura lógica de un DVD-Video.

Autor:
    Isidro Riquelme
"""

from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path


@dataclass
class DvdChapter:
    """
    Representa un capítulo de un título DVD-Video.
    """

    number: int
    duration: timedelta | None = None


@dataclass
class DvdTitle:
    """
    Representa un título de un DVD-Video.
    """

    number: int
    vts: int
    duration: timedelta | None = None
    chapters: list[DvdChapter] = field(default_factory=list)


@dataclass
class DvdVideo:
    """
    Representa la información lógica de un DVD-Video.
    """

    drive: Path
    label: str
    titles: list[DvdTitle] = field(default_factory=list)