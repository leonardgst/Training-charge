"""Entrées, paramètres et sorties du moteur : enregistrements immuables."""

import datetime
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum


@dataclass(frozen=True)
class Parametres:
    """Paramètres de calcul, injectés par l'appelant (`config/calcul.toml`)."""

    facteur_echelle_charge: float
    fenetre_courte_jours: int
    fenetre_longue_jours: int
    reference_jours: int
    reference_min_jours: int
    tolerance_ecart_type_nul: float
    score_poids_min: float
    sensations_reference_jours: int
    sensations_reference_min_entrees: int


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


@dataclass(frozen=True)
class ChargesGlissantes:
    """CE courte et CE longue d'un jour, avec le drapeau de fenêtre incomplète (ADR-0011)."""

    jour: datetime.date
    ce_courte: float
    ce_longue: float
    courte_incomplete: bool
    longue_incomplete: bool


class Etat(StrEnum):
    """État d'une grandeur ; les valeurs sont celles de `attendu.csv`."""

    OK = "ok"
    HISTORIQUE_INSUFFISANT = "historique_insuffisant"
    NON_CALCULABLE = "non_calculable"
    REPONSES_INSUFFISANTES = "reponses_insuffisantes"


@dataclass(frozen=True)
class ZScore:
    """Z-score d'un jour : `valeur` n'existe que si `etat` vaut `Etat.OK`."""

    jour: datetime.date
    valeur: float | None
    etat: Etat


@dataclass(frozen=True)
class IndicateurScore:
    """Indicateur noté qui entre dans le score de sensations (ADR-0010, ADR-0014)."""

    code: str
    borne_min: int
    borne_max: int
    haut_est_bon: bool
    poids: float


@dataclass(frozen=True)
class EntreeSensations:
    """Réponses d'un joueur pour un jour, par code d'indicateur."""

    jour: datetime.date
    reponses: Mapping[str, int]


@dataclass(frozen=True)
class ScoreEntree:
    """Score d'une entrée, dans [0, 1] (1 = meilleur état), défini si `etat` vaut OK."""

    jour: datetime.date
    valeur: float | None
    etat: Etat
