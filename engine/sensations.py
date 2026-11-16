"""Score de sensations (ADR-0014) et z-score de sensations (ADR-0015)."""

import datetime
from collections.abc import Sequence

from engine.modeles import (
    CelluleSensations,
    DetailSensations,
    EntreeSensations,
    Etat,
    IndicateurScore,
    Parametres,
    ScoreEntree,
    ZScore,
)
from engine.zscore import zscore

# Écart toléré sur la part de poids répondue (somme de décimaux représentée en flottants).
TOLERANCE_POIDS = 1e-12
# Le score, dans [0, 1], s'affiche sur 10 (ADR-0014, Q5).
ECHELLE_AFFICHAGE = 10
# Longueur de la heatmap de la fiche joueur, en jours.
JOURS_HEATMAP = 7


def _normalise(valeur: int, indicateur: IndicateurScore) -> float:
    """Ramène la réponse dans [0, 1] par les bornes, 1 étant le meilleur état."""
    if not indicateur.borne_min <= valeur <= indicateur.borne_max:
        raise ValueError(f"{indicateur.code} : {valeur} hors des bornes de l'indicateur")
    u = (valeur - indicateur.borne_min) / (indicateur.borne_max - indicateur.borne_min)
    return u if indicateur.haut_est_bon else 1 - u


def score_entree(
    entree: EntreeSensations, indicateurs: Sequence[IndicateurScore], parametres: Parametres
) -> ScoreEntree:
    """Σ(poids × u) / Σ(poids) sur les indicateurs inclus et répondus.

    Chaque réponse est normalisée par ses bornes avant d'être agrégée. En dessous de
    `score_poids_min` du poids total des indicateurs inclus, l'état est
    `REPONSES_INSUFFISANTES`. Les réponses à un indicateur absent de `indicateurs` sont
    ignorées.
    """
    poids_total = sum(i.poids for i in indicateurs)
    repondus = [i for i in indicateurs if i.code in entree.reponses]
    poids_repondu = sum(i.poids for i in repondus)
    if (
        poids_repondu <= 0
        or poids_repondu < parametres.score_poids_min * poids_total - TOLERANCE_POIDS
    ):
        return ScoreEntree(entree.jour, None, Etat.REPONSES_INSUFFISANTES)
    somme = sum(i.poids * _normalise(entree.reponses[i.code], i) for i in repondus)
    return ScoreEntree(entree.jour, somme / poids_repondu, Etat.OK)


def scores(
    entrees: Sequence[EntreeSensations],
    indicateurs: Sequence[IndicateurScore],
    parametres: Parametres,
) -> list[ScoreEntree]:
    """Score de chaque entrée, triées par date."""
    return [score_entree(e, indicateurs, parametres) for e in sorted(entrees, key=lambda e: e.jour)]


def sensations_z(scores_entrees: Sequence[ScoreEntree], parametres: Parametres) -> list[ZScore]:
    """Z-score de chaque entrée contre les scores des entrées de D − 28 à D − 1.

    Entrée courante exclue ; les entrées sans score sont écartées de la référence. Une
    entrée sans score n'a pas de z-score : son état est `REPONSES_INSUFFISANTES`.
    """
    resultat = []
    for courante in scores_entrees:
        if courante.valeur is None:
            resultat.append(ZScore(courante.jour, None, Etat.REPONSES_INSUFFISANTES))
            continue
        debut = courante.jour - datetime.timedelta(days=parametres.sensations_reference_jours)
        reference = [
            e.valeur
            for e in scores_entrees
            if e.valeur is not None and debut <= e.jour < courante.jour
        ]
        resultat.append(
            zscore(
                courante.jour,
                courante.valeur,
                reference,
                parametres.sensations_reference_min_entrees,
                parametres.tolerance_ecart_type_nul,
            )
        )
    return resultat


def detail_entree(
    entree: EntreeSensations, indicateurs: Sequence[IndicateurScore], parametres: Parametres
) -> DetailSensations:
    """Niveau de chaque indicateur du score et total sur 10 pour une entrée.

    Les niveaux et le total viennent des mêmes bornes, du même sens et du même poids minimal
    que `score_entree` : même sous le poids minimal, les niveaux des réponses présentes restent
    donnés, seul le total manque. Les réponses à un indicateur absent de `indicateurs` sont
    ignorées.
    """
    cellules = tuple(
        CelluleSensations(
            i.code,
            entree.reponses[i.code],
            _normalise(entree.reponses[i.code], i) * ECHELLE_AFFICHAGE,
        )
        if i.code in entree.reponses
        else CelluleSensations(i.code, None, None)
        for i in indicateurs
    )
    score = score_entree(entree, indicateurs, parametres)
    total = None if score.valeur is None else score.valeur * ECHELLE_AFFICHAGE
    return DetailSensations(entree.jour, True, cellules, total, score.etat)


def sensations_sur_jours(
    entrees: Sequence[EntreeSensations],
    indicateurs: Sequence[IndicateurScore],
    parametres: Parametres,
    jour: datetime.date,
) -> list[DetailSensations]:
    """Détail des `JOURS_HEATMAP` jours se terminant à `jour`, du plus ancien au plus récent.

    Un jour sans entrée a des cellules vides, sans total ni état. Les entrées hors de la
    fenêtre sont ignorées.
    """
    par_jour = {e.jour: e for e in entrees}
    resultat = []
    for decalage in range(JOURS_HEATMAP - 1, -1, -1):
        courant = jour - datetime.timedelta(days=decalage)
        if courant in par_jour:
            resultat.append(detail_entree(par_jour[courant], indicateurs, parametres))
        else:
            vides = tuple(CelluleSensations(i.code, None, None) for i in indicateurs)
            resultat.append(DetailSensations(courant, False, vides, None, None))
    return resultat


def derniere_entree_detaillee(
    entrees: Sequence[EntreeSensations],
    indicateurs: Sequence[IndicateurScore],
    parametres: Parametres,
    jour: datetime.date,
) -> DetailSensations | None:
    """Détail de l'entrée la plus récente datée au plus tard de `jour`, ou rien."""
    candidates = [e for e in entrees if e.jour <= jour]
    if not candidates:
        return None
    return detail_entree(max(candidates, key=lambda e: e.jour), indicateurs, parametres)
