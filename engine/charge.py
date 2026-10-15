"""Charge de séance et charge du jour sur un calendrier continu (ADR-0007, ADR-0011)."""

import datetime
from collections import defaultdict
from collections.abc import Sequence

from engine.modeles import JourCalcule, Parametres, ParticipationValidee


def charge_seance(participation: ParticipationValidee, parametres: Parametres) -> float:
    """(cardio + musculaire + TETA) / 3 × durée × facteur d'échelle."""
    somme_rpe = participation.rpe_cardio + participation.rpe_musculaire + participation.rpe_teta
    return somme_rpe / 3 * participation.duree_min * parametres.facteur_echelle_charge


def calendrier(
    participations: Sequence[ParticipationValidee], parametres: Parametres, fin: datetime.date
) -> list[JourCalcule]:
    """Une ligne par jour, de la première participation à `fin` incluse.

    Les jours sans séance valent 0 ; deux séances le même jour s'additionnent. Les
    participations datées après `fin` sont ignorées. Sans participation, le calendrier
    est vide : le joueur n'a pas de début de suivi.
    """
    retenues = [p for p in participations if p.jour <= fin]
    if not retenues:
        return []
    par_jour: defaultdict[datetime.date, float] = defaultdict(float)
    for participation in retenues:
        par_jour[participation.jour] += charge_seance(participation, parametres)
    debut = min(par_jour)
    return [
        JourCalcule(jour=jour, charge_jour=par_jour.get(jour, 0.0))
        for jour in (debut + datetime.timedelta(days=i) for i in range((fin - debut).days + 1))
    ]
