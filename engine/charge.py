"""Charge de séance, charge du jour et charges glissantes (ADR-0007, ADR-0011)."""

import datetime
from collections import defaultdict
from collections.abc import Sequence

from engine.modeles import ChargesGlissantes, JourCalcule, Parametres, ParticipationValidee


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


def charges_glissantes(
    jours: Sequence[JourCalcule], parametres: Parametres
) -> list[ChargesGlissantes]:
    """CE courte et CE longue de chaque jour : somme des `fenetre` derniers jours, jour inclus.

    `jours` est un calendrier continu. Au début du calendrier, la somme porte sur les jours
    disponibles et la fenêtre est signalée incomplète.
    """
    resultat = []
    for i, jour in enumerate(jours):
        courte = jours[max(0, i + 1 - parametres.fenetre_courte_jours) : i + 1]
        longue = jours[max(0, i + 1 - parametres.fenetre_longue_jours) : i + 1]
        resultat.append(
            ChargesGlissantes(
                jour=jour.jour,
                ce_courte=sum(j.charge_jour for j in courte),
                ce_longue=sum(j.charge_jour for j in longue),
                courte_incomplete=i + 1 < parametres.fenetre_courte_jours,
                longue_incomplete=i + 1 < parametres.fenetre_longue_jours,
            )
        )
    return resultat
