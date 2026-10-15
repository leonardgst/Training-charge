"""CE courte et CE longue du moteur (C3 sans base).

Les valeurs attendues sont calculées à la main depuis l'ADR-0011 : somme des charges du jour
sur les 7 (ou 28) derniers jours, jour courant inclus.
"""

import datetime
import math

from engine.charge import calendrier, charges_glissantes
from engine.modeles import JourCalcule, Parametres, ParticipationValidee

PARAMETRES = Parametres(10, 7, 28, 28, 21, 1e-9)
LUNDI = datetime.date(2026, 1, 5)


def _jours(*charges: float) -> list[JourCalcule]:
    return [JourCalcule(LUNDI + datetime.timedelta(days=i), c) for i, c in enumerate(charges)]


def test_un_calendrier_vide_n_a_aucune_charge_glissante() -> None:
    assert charges_glissantes([], PARAMETRES) == []


def test_au_debut_la_somme_porte_sur_les_jours_disponibles_et_la_fenetre_est_incomplete() -> None:
    premier, deuxieme = charges_glissantes(_jours(100, 50), PARAMETRES)
    assert (premier.ce_courte, premier.ce_longue) == (100, 100)
    assert (deuxieme.ce_courte, deuxieme.ce_longue) == (150, 150)
    assert premier.courte_incomplete and premier.longue_incomplete
    assert deuxieme.courte_incomplete and deuxieme.longue_incomplete


def test_la_fenetre_courte_est_complete_au_septieme_jour() -> None:
    resultat = charges_glissantes(_jours(*[10] * 7), PARAMETRES)
    assert [r.courte_incomplete for r in resultat] == [True] * 6 + [False]
    assert resultat[6].ce_courte == 70
    assert all(r.longue_incomplete for r in resultat)


def test_la_charge_sortie_de_la_fenetre_courte_n_est_plus_comptee() -> None:
    # Jour 1 : 700 ; puis six jours à 0 ; le huitième jour la charge du jour 1 sort.
    resultat = charges_glissantes(_jours(700, 0, 0, 0, 0, 0, 0, 0), PARAMETRES)
    assert resultat[6].ce_courte == 700
    assert resultat[7].ce_courte == 0
    assert resultat[7].ce_longue == 700


def test_la_ce_courte_decroit_les_jours_sans_seance() -> None:
    # Séances de 100 les jours 1 et 2, puis des zéros : 100, 200, 200, 200, 200, 200, 200, 100, 0.
    resultat = charges_glissantes(_jours(100, 100, 0, 0, 0, 0, 0, 0, 0), PARAMETRES)
    assert [r.ce_courte for r in resultat] == [100, 200, 200, 200, 200, 200, 200, 100, 0]


def test_la_fenetre_longue_est_complete_au_vingt_huitieme_jour() -> None:
    resultat = charges_glissantes(_jours(*[1] * 29), PARAMETRES)
    assert [r.longue_incomplete for r in resultat] == [True] * 27 + [False, False]
    assert resultat[27].ce_longue == 28
    assert resultat[28].ce_longue == 28
    assert resultat[28].ce_courte == 7


def test_les_fenetres_viennent_des_parametres() -> None:
    resultat = charges_glissantes(_jours(1, 2, 4, 8), Parametres(10, 2, 3, 28, 21, 1e-9))
    assert [r.ce_courte for r in resultat] == [1, 3, 6, 12]
    assert [r.ce_longue for r in resultat] == [1, 3, 7, 14]
    assert [r.courte_incomplete for r in resultat] == [True, False, False, False]
    assert [r.longue_incomplete for r in resultat] == [True, True, False, False]


def test_de_bout_en_bout_depuis_les_participations() -> None:
    # (5 + 6 + 4) / 3 × 60 × 10 = 3000 le lundi, puis trois jours sans séance.
    participations = [ParticipationValidee(LUNDI, 60, 5, 6, 4)]
    jours = calendrier(participations, PARAMETRES, fin=LUNDI + datetime.timedelta(days=3))
    assert all(math.isclose(r.ce_courte, 3000.0) for r in charges_glissantes(jours, PARAMETRES))
