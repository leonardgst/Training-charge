"""Badge du questionnaire dans la grille d'une séance : fonction pure, sans requête."""

import datetime
from typing import Literal


def etat_questionnaire(
    jour: datetime.date, aujourd_hui: datetime.date, jours_questionnaire: list[int], recu: bool
) -> Literal["recu", "manquant"] | None:
    """État du badge d'un joueur à la date `jour` d'une séance (R22, ADR-0017, Q3).

    `"recu"` si une entrée existe à cette date, quel que soit le jour de la semaine ;
    `"manquant"` si c'est un jour de questionnaire de sa catégorie, déjà arrivé, sans entrée
    (le jour même, le joueur peut encore répondre) ; `None` (un tiret) sinon.
    """
    if recu:
        return "recu"
    if jour <= aujourd_hui and jour.weekday() in jours_questionnaire:
        return "manquant"
    return None
