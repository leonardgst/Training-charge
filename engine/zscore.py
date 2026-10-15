"""Z-score d'intensité (ADR-0012) : chaque joueur n'est comparé qu'à lui-même."""

import datetime
import statistics
from collections.abc import Sequence

from engine.modeles import ChargesGlissantes, Etat, Parametres, ZScore


def intensite(glissantes: Sequence[ChargesGlissantes], parametres: Parametres) -> list[ZScore]:
    """(CE courte du jour − m) / s, sur les CE courtes des `reference_jours` jours précédents.

    La référence s'arrête à la veille : le jour courant n'en fait jamais partie. Seuls
    comptent les jours dont la CE courte repose sur une fenêtre complète. En dessous de
    `reference_min_jours` de ceux-là, l'état est `HISTORIQUE_INSUFFISANT` ; un écart-type
    (d'échantillon) nul ou négligeable donne `NON_CALCULABLE`, jamais une division.
    """
    resultat = []
    for i, courant in enumerate(glissantes):
        debut = max(0, i - parametres.reference_jours)
        reference = [g.ce_courte for g in glissantes[debut:i] if not g.courte_incomplete]
        resultat.append(_zscore(courant.jour, courant.ce_courte, reference, parametres))
    return resultat


def _zscore(
    jour: datetime.date, valeur: float, reference: Sequence[float], parametres: Parametres
) -> ZScore:
    if len(reference) < parametres.reference_min_jours:
        return ZScore(jour, None, Etat.HISTORIQUE_INSUFFISANT)
    moyenne = statistics.fmean(reference)
    ecart_type = statistics.stdev(reference)
    if ecart_type <= parametres.tolerance_ecart_type_nul * max(1.0, abs(moyenne)):
        return ZScore(jour, None, Etat.NON_CALCULABLE)
    return ZScore(jour, (valeur - moyenne) / ecart_type, Etat.OK)
