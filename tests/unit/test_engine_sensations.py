"""Score et z-score de sensations du moteur (C7, C8, C11, C12, C13 sans base).

Valeurs attendues calculées à la main depuis les ADR-0014 et ADR-0015.
"""

import datetime
import math

import pytest

from engine.modeles import EntreeSensations, Etat, IndicateurScore, Parametres, ScoreEntree
from engine.sensations import score_entree, scores, sensations_z

PARAMETRES = Parametres(10, 7, 28, 28, 21, 1e-9, 0.5, 28, 6)
DEBUT = datetime.date(2026, 1, 5)

PLAISIR = IndicateurScore("plaisir", 0, 10, True, 1.0)
FATIGUE = IndicateurScore("fatigue", 0, 10, False, 1.0)
SOMMEIL = IndicateurScore("sommeil", 1, 5, True, 2.0)


def _entree(decalage: int = 0, **reponses: int) -> EntreeSensations:
    return EntreeSensations(DEBUT + datetime.timedelta(days=decalage), reponses)


def test_c11_deux_echelles_sont_normalisees_avant_d_etre_agregees() -> None:
    # plaisir 5/10 → 0,5 ; sommeil 4 sur 1–5 → 0,75 ; poids 1 et 2 : (0,5 + 2 × 0,75) / 3.
    resultat = score_entree(_entree(plaisir=5, sommeil=4), [PLAISIR, SOMMEIL], PARAMETRES)
    assert resultat.etat is Etat.OK
    assert resultat.valeur is not None and math.isclose(resultat.valeur, 2.0 / 3)


def test_c12_un_indicateur_bas_bon_est_inverse() -> None:
    resultat = score_entree(_entree(plaisir=8, fatigue=2), [PLAISIR, FATIGUE], PARAMETRES)
    assert resultat.valeur is not None and math.isclose(resultat.valeur, 0.8)  # (0,8 + 0,8) / 2


def test_le_meilleur_et_le_pire_etat_valent_un_et_zero() -> None:
    meilleur = score_entree(_entree(plaisir=10, fatigue=0), [PLAISIR, FATIGUE], PARAMETRES)
    pire = score_entree(_entree(plaisir=0, fatigue=10), [PLAISIR, FATIGUE], PARAMETRES)
    assert (meilleur.valeur, pire.valeur) == (1.0, 0.0)


def test_c13_une_reponse_manquante_donne_un_score_sur_les_reponses_presentes() -> None:
    # Poids répondu 1 sur 2 = 50 % : suffisant ; score = u(plaisir) seul.
    resultat = score_entree(_entree(plaisir=3), [PLAISIR, FATIGUE], PARAMETRES)
    assert resultat.valeur is not None and math.isclose(resultat.valeur, 0.3)


def test_c13_sous_le_poids_minimal_les_reponses_sont_insuffisantes() -> None:
    # Poids répondu 1 sur 4 (sommeil pèse 2) : 25 % < 50 %.
    resultat = score_entree(_entree(plaisir=3), [PLAISIR, FATIGUE, SOMMEIL], PARAMETRES)
    assert (resultat.valeur, resultat.etat) == (None, Etat.REPONSES_INSUFFISANTES)


def test_une_entree_sans_reponse_est_insuffisante() -> None:
    assert score_entree(_entree(), [PLAISIR], PARAMETRES).etat is Etat.REPONSES_INSUFFISANTES


def test_sans_indicateur_inclus_aucun_score() -> None:
    assert score_entree(_entree(plaisir=5), [], PARAMETRES).etat is Etat.REPONSES_INSUFFISANTES


def test_les_reponses_a_un_indicateur_hors_score_sont_ignorees() -> None:
    a = score_entree(_entree(plaisir=5, heure_coucher=1380), [PLAISIR], PARAMETRES)
    assert a.valeur == 0.5


def test_une_reponse_hors_bornes_est_refusee() -> None:
    with pytest.raises(ValueError, match="hors des bornes"):
        score_entree(_entree(plaisir=11), [PLAISIR], PARAMETRES)


def test_le_poids_exactement_minimal_suffit() -> None:
    quatre = [IndicateurScore(f"i{k}", 0, 10, True, 0.1) for k in range(4)]
    resultat = score_entree(_entree(i0=10, i1=10), quatre, PARAMETRES)
    assert resultat.etat is Etat.OK


def test_les_scores_sont_tries_par_date() -> None:
    resultat = scores([_entree(2, plaisir=10), _entree(0, plaisir=0)], [PLAISIR], PARAMETRES)
    assert [r.jour for r in resultat] == [DEBUT, DEBUT + datetime.timedelta(days=2)]


def _scores(*valeurs: float | None, pas: int = 1) -> list[ScoreEntree]:
    return [
        ScoreEntree(
            DEBUT + datetime.timedelta(days=i * pas),
            v,
            Etat.OK if v is not None else Etat.REPONSES_INSUFFISANTES,
        )
        for i, v in enumerate(valeurs)
    ]


def test_zscore_de_sensations_calcule_a_la_main() -> None:
    # Référence 0,2 0,4 0,6 0,8 0,4 0,6 : m = 0,5 ; s² = 0,28/5 ; courant 0,9.
    reference = [0.2, 0.4, 0.6, 0.8, 0.4, 0.6]
    z = sensations_z(_scores(*reference, 0.9), PARAMETRES)[6]
    ecart = math.sqrt(sum((x - 0.5) ** 2 for x in reference) / 5)
    assert z.etat is Etat.OK
    assert z.valeur is not None and math.isclose(z.valeur, 0.4 / ecart)


def test_c8_moins_de_six_entrees_de_reference_donne_historique_insuffisant() -> None:
    z = sensations_z(_scores(0.2, 0.4, 0.6, 0.8, 0.5, 0.9), PARAMETRES)
    assert z[5].etat is Etat.HISTORIQUE_INSUFFISANT  # 5 entrées de référence
    assert z[0].etat is Etat.HISTORIQUE_INSUFFISANT  # aucune


def test_c7_des_reponses_toujours_identiques_sont_non_calculables() -> None:
    z = sensations_z(_scores(*[0.6] * 8), PARAMETRES)
    assert (z[7].valeur, z[7].etat) == (None, Etat.NON_CALCULABLE)


def test_les_entrees_sans_score_sont_ecartees_de_la_reference() -> None:
    # 5 scores et 2 entrées insuffisantes avant la courante : 5 points de référence seulement.
    z = sensations_z(_scores(0.2, None, 0.4, 0.6, None, 0.8, 0.5, 0.9), PARAMETRES)
    assert z[7].etat is Etat.HISTORIQUE_INSUFFISANT
    assert z[1].etat is Etat.REPONSES_INSUFFISANTES  # une entrée sans score n'a pas de z


def test_la_reference_couvre_les_28_jours_precedents_seulement() -> None:
    # Pas de 5 jours : pour l'entrée 8 (jour 40), la référence est les jours 12 à 39 :
    # entrées 3 à 7 seulement (jours 15 à 35), soit 5 < 6 ; l'entrée 0 (jour 0) est trop ancienne.
    z = sensations_z(_scores(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, pas=5), PARAMETRES)
    assert z[8].etat is Etat.HISTORIQUE_INSUFFISANT
    # Pour l'entrée 7 (jour 35) : jours 7 à 34 = entrées 2 à 6, soit 5 aussi.
    assert z[7].etat is Etat.HISTORIQUE_INSUFFISANT


def test_la_borne_de_28_jours_est_incluse_et_l_entree_courante_exclue() -> None:
    # Six entrées à D − 28, D − 23, …, D − 3 puis la courante : six points de référence.
    valeurs = [0.2, 0.4, 0.6, 0.8, 0.5, 0.7]
    entrees = [
        ScoreEntree(DEBUT + datetime.timedelta(days=5 * i), v, Etat.OK)
        for i, v in enumerate(valeurs)
    ]
    courante = ScoreEntree(DEBUT + datetime.timedelta(days=28), 0.9, Etat.OK)
    z = sensations_z([*entrees, courante], PARAMETRES)[-1]
    assert z.etat is Etat.OK
