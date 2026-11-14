"""« Forme actuelle » d'un joueur au jour D (R14, R23, ADR-0013, ADR-0018).

Un point par joueur : en abscisse l'intensité du jour D, en ordonnée les sensations (z) de
l'entrée la plus récente datée de D − `fraicheur_entree_jours` à D, et une couleur
(intensité − sensations) / 2 bornée à ±`couleur_borne`. Sans point, un état explique
pourquoi. Aucune donnée datée après D n'entre dans le calcul (C9).
"""

import datetime
from collections.abc import Sequence

from engine.charge import calendrier, charges_glissantes
from engine.modeles import (
    EntreeSensations,
    Etat,
    EtatForme,
    FormeActuelle,
    IndicateurScore,
    Parametres,
    ParticipationValidee,
    PointForme,
    ZScore,
)
from engine.sensations import scores, sensations_z
from engine.zscore import intensite as intensites

# État d'un z-score sans valeur, repris tel quel par « Forme actuelle ».
_ETAT_DU_ZSCORE = {
    Etat.HISTORIQUE_INSUFFISANT: EtatForme.HISTORIQUE_INSUFFISANT,
    Etat.NON_CALCULABLE: EtatForme.NON_CALCULABLE,
    Etat.REPONSES_INSUFFISANTES: EtatForme.REPONSES_INSUFFISANTES,
}


def entree_retenue(
    z_entrees: Sequence[ZScore], parametres: Parametres, jour: datetime.date
) -> ZScore | None:
    """Z-score de l'entrée la plus récente datée de `jour` − fraîcheur à `jour` inclus.

    Aucune entrée dans la fenêtre : `None`. Pas de repli sur une entrée plus ancienne quand
    la plus récente n'a pas de z-score : elle est retenue avec son état.
    """
    debut = jour - datetime.timedelta(days=parametres.fraicheur_entree_jours)
    recentes = [z for z in z_entrees if debut <= z.jour <= jour]
    return max(recentes, key=lambda z: z.jour, default=None)


def couleur(intensite: float, sensations: float, parametres: Parametres) -> float:
    """(intensité − sensations) / 2, bornée entre −`couleur_borne` et `couleur_borne`.

    Elle croît avec l'intensité et quand les sensations se dégradent (ADR-0018, Q2).
    """
    borne = parametres.couleur_borne
    return max(-borne, min(borne, (intensite - sensations) / 2))


def absent_depuis(
    participations: Sequence[ParticipationValidee], parametres: Parametres, jour: datetime.date
) -> int | None:
    """Jours écoulés depuis la dernière participation, si la fenêtre courte n'en a aucune.

    La fenêtre courte couvre les `fenetre_courte_jours` jours qui finissent à `jour`. Une
    participation à charge nulle est une présence. Sans aucune participation, le suivi n'a
    pas commencé : le joueur n'est pas « absent » (`None`).
    """
    passees = [p.jour for p in participations if p.jour <= jour]
    if not passees:
        return None
    ecart = (jour - max(passees)).days
    return ecart if ecart >= parametres.fenetre_courte_jours else None


def _etat_et_point(
    intensite_du_jour: ZScore | None,
    sensations: ZScore | None,
    absent: int | None,
    parametres: Parametres,
) -> tuple[EtatForme, PointForme | None]:
    """Premier état qui empêche le point, dans l'ordre : absence, intensité, sensations."""
    if absent is not None:
        return EtatForme.ABSENT, None
    if intensite_du_jour is None:
        return EtatForme.HISTORIQUE_INSUFFISANT, None
    x = intensite_du_jour.valeur
    if x is None:
        return _ETAT_DU_ZSCORE[intensite_du_jour.etat], None
    if sensations is None:
        return EtatForme.PAS_D_ENTREE_RECENTE, None
    y = sensations.valeur
    if y is None:
        return _ETAT_DU_ZSCORE[sensations.etat], None
    return EtatForme.OK, PointForme(x, y, couleur(x, y, parametres))


def forme_actuelle(
    participations: Sequence[ParticipationValidee],
    entrees: Sequence[EntreeSensations],
    indicateurs: Sequence[IndicateurScore],
    parametres: Parametres,
    jour: datetime.date,
) -> FormeActuelle:
    """Situation d'un joueur au jour `jour` : un point, ou l'état qui l'empêche.

    Les participations et les entrées datées après `jour` sont ignorées. L'absence passe
    avant tout (ADR-0013, Q2) : un joueur sans participation sur la fenêtre courte est
    listé « absent depuis N jours », même si son intensité se calcule. Viennent ensuite
    l'état de l'intensité, puis l'absence d'entrée récente, puis l'état des sensations.
    """
    passees = [p for p in participations if p.jour <= jour]
    z_intensite = intensites(
        charges_glissantes(calendrier(passees, parametres, jour), parametres), parametres
    )
    intensite_du_jour = z_intensite[-1] if z_intensite else None

    retenues = [e for e in entrees if e.jour <= jour]
    if len({e.jour for e in retenues}) != len(retenues):
        raise ValueError("deux entrées de sensations le même jour pour un joueur")
    z_sensations = sensations_z(scores(retenues, indicateurs, parametres), parametres)
    sensations = entree_retenue(z_sensations, parametres, jour)

    absent = absent_depuis(passees, parametres, jour)
    etat, point = _etat_et_point(intensite_du_jour, sensations, absent, parametres)
    return FormeActuelle(
        jour=jour,
        etat=etat,
        point=point,
        intensite=intensite_du_jour,
        sensations=sensations,
        jour_entree=sensations.jour if sensations is not None else None,
        age_entree_jours=(jour - sensations.jour).days if sensations is not None else None,
        absent_depuis_jours=absent,
    )
