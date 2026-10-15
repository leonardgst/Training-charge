"""Z-score d'intensité du moteur (C4, C6, C7, C8, C14 sans base).

Valeurs attendues calculées à la main depuis l'ADR-0012 : (CE courte − m) / s, m et s sur
les CE courtes des jours précédents, jour courant exclu, écart-type d'échantillon.
"""

import datetime
import math

from engine.charge import calendrier, charges_glissantes
from engine.modeles import ChargesGlissantes, Etat, Parametres, ParticipationValidee
from engine.zscore import intensite

PARAMETRES = Parametres(10, 7, 28, 28, 21, 1e-9)
DEBUT = datetime.date(2026, 1, 5)


def _glissantes(*ce: float, incompletes: int = 0) -> list[ChargesGlissantes]:
    return [
        ChargesGlissantes(DEBUT + datetime.timedelta(days=i), c, c, i < incompletes, False)
        for i, c in enumerate(ce)
    ]


def test_zscore_calcule_a_la_main() -> None:
    # Référence 1, 2, 3, 4 : m = 2,5 ; s² = 5/3 ; valeur du jour 6 : z = 3,5 / √(5/3).
    parametres = Parametres(10, 7, 28, 28, 4, 1e-9)
    z = intensite(_glissantes(1, 2, 3, 4, 6), parametres)[4]
    assert z.etat is Etat.OK
    assert z.valeur is not None
    assert math.isclose(z.valeur, 3.5 / math.sqrt(5 / 3))


def test_le_jour_courant_est_exclu_de_la_reference() -> None:
    # Avec le point courant, z serait borné par (n − 1)/√n ; sans lui il le dépasse.
    parametres = Parametres(10, 7, 28, 28, 4, 1e-9)
    z = intensite(_glissantes(1, 2, 1, 2, 1000), parametres)[4]
    assert z.valeur is not None and z.valeur > 1000


def test_historique_insuffisant_sous_le_minimum_de_jours_de_reference() -> None:
    resultat = intensite(_glissantes(*[1.0, 2.0] * 11), PARAMETRES)  # 22 jours
    assert [r.etat for r in resultat[:21]] == [Etat.HISTORIQUE_INSUFFISANT] * 21
    assert resultat[21].etat is Etat.OK  # 21 jours de référence


def test_les_fenetres_incompletes_ne_comptent_pas_dans_la_reference() -> None:
    # 6 premiers jours à fenêtre incomplète : le premier z a lieu 21 jours complets plus tard.
    resultat = intensite(_glissantes(*[1.0, 2.0] * 14, incompletes=6), PARAMETRES)
    premiers = [i for i, r in enumerate(resultat) if r.etat is not Etat.HISTORIQUE_INSUFFISANT]
    assert premiers[0] == 6 + 21


def test_la_reference_est_limitee_aux_28_jours_precedents() -> None:
    # Un jour 0 extrême sort de la référence du jour 29 (jours 1 à 28).
    ce = [1e6] + [1.0, 2.0] * 14 + [3.0]
    assert len(ce) == 30
    z = intensite(_glissantes(*ce), PARAMETRES)[29]
    reference = ce[1:29]
    moyenne = sum(reference) / 28
    ecart = math.sqrt(sum((x - moyenne) ** 2 for x in reference) / 27)
    assert z.valeur is not None
    assert math.isclose(z.valeur, (3.0 - moyenne) / ecart)


def test_historique_constant_est_non_calculable() -> None:
    resultat = intensite(_glissantes(*[500.0] * 30), PARAMETRES)
    assert resultat[29].etat is Etat.NON_CALCULABLE
    assert resultat[29].valeur is None


def test_ecart_type_negligeable_est_non_calculable() -> None:
    # Bruit d'arrondi de 1e-7 sur 1e6 : s ≈ 5e-8 ≤ 1e-9 × 1e6 = 1e-3.
    ce = [1e6 + (1e-7 if i % 2 else 0.0) for i in range(30)]
    assert intensite(_glissantes(*ce), PARAMETRES)[29].etat is Etat.NON_CALCULABLE


def test_ecart_type_nul_avec_moyenne_nulle_est_non_calculable() -> None:
    assert intensite(_glissantes(*[0.0] * 30), PARAMETRES)[29].etat is Etat.NON_CALCULABLE


def test_charge_extreme_apres_un_historique_regulier() -> None:
    ce = [100.0, 120.0] * 14 + [5000.0]
    z = intensite(_glissantes(*ce), PARAMETRES)[28]
    assert z.valeur is not None and z.valeur > 2


def _jours_reguliers() -> list[ParticipationValidee]:
    return [
        ParticipationValidee(DEBUT + datetime.timedelta(days=i), 60, 4 + i % 3, 5, 6 - i % 2)
        for i in range(0, 40, 2)
    ] + [ParticipationValidee(DEBUT + datetime.timedelta(days=40), 120, 10, 10, 10)]


def test_charges_multipliees_zscores_identiques() -> None:
    fin = DEBUT + datetime.timedelta(days=40)
    un, sept = PARAMETRES, Parametres(70, 7, 28, 28, 21, 1e-9)
    jours_un = calendrier(_jours_reguliers(), un, fin)
    jours_sept = calendrier(_jours_reguliers(), sept, fin)
    z_un = intensite(charges_glissantes(jours_un, un), un)
    z_sept = intensite(charges_glissantes(jours_sept, sept), sept)
    assert z_un[-1].valeur is not None and z_sept[-1].valeur is not None
    assert math.isclose(jours_sept[-1].charge_jour, 7 * jours_un[-1].charge_jour)
    assert all(
        a.etat == b.etat
        and (a.valeur is None or math.isclose(a.valeur, b.valeur or 0, abs_tol=1e-9))
        for a, b in zip(z_un, z_sept, strict=True)
    )


def test_absent_dix_jours_la_ce_courte_tombe_a_zero_et_l_intensite_est_recalculee() -> None:
    participations = [
        ParticipationValidee(DEBUT + datetime.timedelta(days=i), 60, 4 + i % 3, 5, 6)
        for i in range(0, 40)
        if i % 2 == 0 or i % 3 == 0
    ]
    fin = DEBUT + datetime.timedelta(days=50)
    jours = calendrier(participations, PARAMETRES, fin)
    glissantes = charges_glissantes(jours, PARAMETRES)
    resultat = intensite(glissantes, PARAMETRES)
    assert glissantes[-1].ce_courte == 0.0
    # Dix jours sans séance : un z-score défini et négatif chaque jour, aucune ligne manquante.
    assert len(jours) == 51
    assert all(r.etat is Etat.OK and r.valeur is not None and r.valeur < 0 for r in resultat[-10:])
