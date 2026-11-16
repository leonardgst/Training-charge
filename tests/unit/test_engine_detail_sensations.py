"""Détail des sensations pour la fiche joueur : niveaux par indicateur et total sur 10.

Valeurs attendues calculées à la main depuis l'ADR-0014 (Q1, Q2, Q5).
"""

import datetime
import math

import pytest

from engine.modeles import EntreeSensations, Etat, IndicateurScore, Parametres
from engine.sensations import (
    ECHELLE_AFFICHAGE,
    derniere_entree_detaillee,
    detail_entree,
    sensations_sur_jours,
)

PARAMETRES = Parametres(10, 7, 28, 28, 21, 1e-9, 0.5, 28, 6, 3, 3)
JOUR = datetime.date(2026, 11, 14)

PLAISIR = IndicateurScore("plaisir", 0, 10, True, 1.0)
FATIGUE = IndicateurScore("fatigue", 0, 10, False, 1.0)
SOMMEIL = IndicateurScore("sommeil", 1, 5, True, 2.0)


def _entree(decalage: int, **reponses: int) -> EntreeSensations:
    return EntreeSensations(JOUR - datetime.timedelta(days=decalage), reponses)


def test_l_echelle_d_affichage_est_10() -> None:
    assert ECHELLE_AFFICHAGE == 10


def test_le_niveau_d_un_indicateur_est_normalise_et_sur_10() -> None:
    # sommeil 4 sur 1–5 → u = 0,75 → niveau 7,5.
    detail = detail_entree(_entree(0, sommeil=4), [SOMMEIL], PARAMETRES)
    cellule = detail.cellules[0]
    assert (cellule.code, cellule.valeur) == ("sommeil", 4)
    assert cellule.niveau is not None and math.isclose(cellule.niveau, 7.5)


def test_un_indicateur_bas_bon_est_inverse_dans_le_niveau() -> None:
    # fatigue 2 sur 0–10, bas = bon → u = 0,8 → niveau 8 : 10 est toujours le meilleur état.
    detail = detail_entree(_entree(0, fatigue=2), [FATIGUE], PARAMETRES)
    assert detail.cellules[0].niveau == pytest.approx(8.0)


def test_le_total_est_le_score_du_moteur_sur_10() -> None:
    # Même cas que C11 : score 2/3, affiché 6,67 sur 10.
    detail = detail_entree(_entree(0, plaisir=5, sommeil=4), [PLAISIR, SOMMEIL], PARAMETRES)
    assert detail.etat is Etat.OK
    assert detail.total is not None and math.isclose(detail.total, 20.0 / 3)


def test_un_indicateur_sans_reponse_a_une_cellule_vide() -> None:
    detail = detail_entree(_entree(0, plaisir=3), [PLAISIR, FATIGUE], PARAMETRES)
    manquante = detail.cellules[1]
    assert (manquante.code, manquante.valeur, manquante.niveau) == ("fatigue", None, None)
    # La réponse présente pèse 1 sur 2 = 50 % : le total existe.
    assert detail.total is not None and math.isclose(detail.total, 3.0)


def test_sous_le_poids_minimal_pas_de_total_mais_les_niveaux_restent() -> None:
    detail = detail_entree(_entree(0, plaisir=3), [PLAISIR, SOMMEIL], PARAMETRES)
    assert detail.etat is Etat.REPONSES_INSUFFISANTES
    assert detail.total is None
    assert detail.cellules[0].niveau == pytest.approx(3.0)


def test_une_reponse_hors_bornes_est_refusee() -> None:
    with pytest.raises(ValueError):
        detail_entree(_entree(0, plaisir=11), [PLAISIR], PARAMETRES)


def test_les_reponses_a_un_indicateur_hors_score_sont_ignorees() -> None:
    detail = detail_entree(_entree(0, plaisir=5, autre=99), [PLAISIR], PARAMETRES)
    assert [c.code for c in detail.cellules] == ["plaisir"]


def test_sept_jours_se_terminent_au_jour_demande_dans_l_ordre() -> None:
    jours = sensations_sur_jours([_entree(0, plaisir=5)], [PLAISIR], PARAMETRES, JOUR)
    assert len(jours) == 7
    assert jours[0].jour == JOUR - datetime.timedelta(days=6)
    assert jours[-1].jour == JOUR


def test_un_jour_sans_entree_n_a_ni_total_ni_etat() -> None:
    jours = sensations_sur_jours([_entree(0, plaisir=5)], [PLAISIR], PARAMETRES, JOUR)
    vide = jours[0]
    assert (vide.a_entree, vide.total, vide.etat) == (False, None, None)
    assert all(c.valeur is None and c.niveau is None for c in vide.cellules)
    assert jours[-1].a_entree and jours[-1].total == pytest.approx(5.0)


def test_les_entrees_hors_de_la_fenetre_sont_ignorees() -> None:
    entrees = [_entree(7, plaisir=1), _entree(-1, plaisir=2)]  # veille de la fenêtre, lendemain
    jours = sensations_sur_jours(entrees, [PLAISIR], PARAMETRES, JOUR)
    assert not any(j.a_entree for j in jours)


def test_la_fenetre_inclut_le_septieme_jour() -> None:
    jours = sensations_sur_jours([_entree(6, plaisir=4)], [PLAISIR], PARAMETRES, JOUR)
    assert jours[0].a_entree and jours[0].total == pytest.approx(4.0)


def test_la_derniere_entree_est_la_plus_recente_au_plus_tard_du_jour() -> None:
    entrees = [_entree(10, plaisir=1), _entree(2, plaisir=6), _entree(-1, plaisir=9)]
    derniere = derniere_entree_detaillee(entrees, [PLAISIR], PARAMETRES, JOUR)
    assert derniere is not None
    assert derniere.jour == JOUR - datetime.timedelta(days=2)
    assert derniere.total == pytest.approx(6.0)


def test_sans_entree_pas_de_derniere_entree() -> None:
    assert derniere_entree_detaillee([], [PLAISIR], PARAMETRES, JOUR) is None
    assert derniere_entree_detaillee([_entree(-1, plaisir=9)], [PLAISIR], PARAMETRES, JOUR) is None
