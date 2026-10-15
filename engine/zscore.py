"""Z-scores d'intensité (ADR-0012) et de sensations (ADR-0015) : chaque joueur n'est comparé
qu'à lui-même."""

import datetime
import statistics
from collections.abc import Sequence

from engine.modeles import ChargesGlissantes, Etat, Parametres, ZScore


def zscore(
    jour: datetime.date,
    valeur: float,
    reference: Sequence[float],
    minimum: int,
    tolerance: float,
) -> ZScore:
    """(valeur − m) / s, m et s étant la moyenne et l'écart-type d'échantillon de `reference`.

    Sous `minimum` points, l'état est `HISTORIQUE_INSUFFISANT` ; un écart-type nul ou
    négligeable (s ≤ `tolerance` × max(1, |m|)) donne `NON_CALCULABLE`, jamais une division.
    """
    if len(reference) < minimum:
        return ZScore(jour, None, Etat.HISTORIQUE_INSUFFISANT)
    moyenne = statistics.fmean(reference)
    ecart_type = statistics.stdev(reference)
    if ecart_type <= tolerance * max(1.0, abs(moyenne)):
        return ZScore(jour, None, Etat.NON_CALCULABLE)
    return ZScore(jour, (valeur - moyenne) / ecart_type, Etat.OK)


def intensite(glissantes: Sequence[ChargesGlissantes], parametres: Parametres) -> list[ZScore]:
    """Z-score de la CE courte du jour sur les CE courtes des `reference_jours` jours précédents.

    La référence s'arrête à la veille : le jour courant n'en fait jamais partie. Seuls
    comptent les jours dont la CE courte repose sur une fenêtre complète.
    """
    resultat = []
    for i, courant in enumerate(glissantes):
        debut = max(0, i - parametres.reference_jours)
        reference = [g.ce_courte for g in glissantes[debut:i] if not g.courte_incomplete]
        resultat.append(
            zscore(
                courant.jour,
                courant.ce_courte,
                reference,
                parametres.reference_min_jours,
                parametres.tolerance_ecart_type_nul,
            )
        )
    return resultat
