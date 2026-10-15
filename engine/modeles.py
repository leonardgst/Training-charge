"""Entrées, paramètres et sorties du moteur : enregistrements immuables."""

import datetime
from dataclasses import dataclass


@dataclass(frozen=True)
class Parametres:
    """Paramètres de calcul, injectés par l'appelant (`config/calcul.toml`)."""

    facteur_echelle_charge: float


@dataclass(frozen=True)
class ParticipationValidee:
    """Participation d'un joueur à une séance validée, avec ses trois RPE."""

    jour: datetime.date
    duree_min: int
    rpe_cardio: int
    rpe_musculaire: int
    rpe_teta: int


@dataclass(frozen=True)
class JourCalcule:
    """Une ligne du calendrier d'un joueur : un jour, quelles que soient ses séances."""

    jour: datetime.date
    charge_jour: float
