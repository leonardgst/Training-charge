"""« Forme actuelle » du moteur (R14, R23, ADR-0013, ADR-0018 ; C4 sans base).

Valeurs attendues calculées à la main. Les paramètres réduits `PETITS` rendent chaque
référence assez courte pour que sa moyenne et son écart-type se calculent de tête : CE
courte sur 1 jour (la charge du jour), intensité contre les 3 jours précédents (au moins
2), sensations contre au moins 2 entrées, facteur d'échelle 1.
"""

import dataclasses
import datetime
import math

import pytest

from engine.forme import absent_depuis, couleur, entree_retenue, forme_actuelle
from engine.modeles import (
    EntreeSensations,
    Etat,
    EtatForme,
    IndicateurScore,
    Parametres,
    ParticipationValidee,
    ZScore,
)
from tests.reference.harnais import lire_cas, trouver_dossier

D = datetime.date(2026, 2, 5)
PETITS = Parametres(1, 1, 2, 3, 2, 1e-9, 0.5, 28, 2, 3, 3)
STANDARD = Parametres(10, 7, 28, 28, 21, 1e-9, 0.5, 28, 6, 3, 3)
PLAISIR = IndicateurScore("plaisir", 0, 10, True, 1.0)
TOLERANCE = 1e-9


def _jour(decalage: int) -> datetime.date:
    return D + datetime.timedelta(days=decalage)


def _seance(decalage: int, rpe: int) -> ParticipationValidee:
    """100 minutes, trois RPE égaux à `rpe` : charge = rpe × 100 avec `PETITS`."""
    return ParticipationValidee(_jour(decalage), 100, rpe, rpe, rpe)


def _entree(decalage: int, plaisir: int | None) -> EntreeSensations:
    """Score = plaisir / 10 ; `None` : entrée sans aucune réponse notée."""
    return EntreeSensations(_jour(decalage), {} if plaisir is None else {"plaisir": plaisir})


def _z(decalage: int, etat: Etat = Etat.OK) -> ZScore:
    return ZScore(_jour(decalage), 0.0 if etat is Etat.OK else None, etat)


# Charges 100, 200, 300 de D − 3 à D − 1 : m = 200, s = √((100² + 0² + 100²) / 2) = 100.
# Charge 400 le jour D : intensité = (400 − 200) / 100 = 2.
MONTEE = [_seance(-3, 1), _seance(-2, 2), _seance(-1, 3), _seance(0, 4)]
# Scores 0,4, 0,5 et 0,6 de D − 6 à D − 4 : m = 0,5, s = √((0,1² + 0² + 0,1²) / 2) = 0,1.
# Ces trois entrées sont hors de la fenêtre de fraîcheur (D − 3 à D).
REFERENCE = [_entree(-6, 4), _entree(-5, 5), _entree(-4, 6)]


# --- Point, couleur -------------------------------------------------------------------


def test_le_point_reunit_l_intensite_du_jour_et_les_sensations_de_l_entree_retenue() -> None:
    # Entrée de D − 1 à 0,3 : sensations = (0,3 − 0,5) / 0,1 = −2 ; couleur (2 + 2) / 2 = 2.
    forme = forme_actuelle(MONTEE, [*REFERENCE, _entree(-1, 3)], [PLAISIR], PETITS, D)

    assert forme.jour == D
    assert forme.etat is EtatForme.OK
    assert forme.point is not None
    assert forme.point.intensite == pytest.approx(2.0, abs=TOLERANCE)
    assert forme.point.sensations == pytest.approx(-2.0, abs=TOLERANCE)
    assert forme.point.couleur == pytest.approx(2.0, abs=TOLERANCE)
    assert (forme.jour_entree, forme.age_entree_jours, forme.absent_depuis_jours) == (
        _jour(-1),
        1,
        None,
    )
    assert forme.intensite is not None and forme.intensite.etat is Etat.OK
    assert forme.sensations is not None and forme.sensations.jour == _jour(-1)


@pytest.mark.parametrize(
    ("intensite", "sensations", "attendue"),
    [
        (2.0, -2.0, 2.0),  # (2 + 2) / 2
        (1.0, 2.0, -0.5),  # (1 − 2) / 2
        (0.0, 0.0, 0.0),
        (2.0, -4.0, 3.0),  # (2 + 4) / 2 = 3 : sur la borne
        (2.0, -5.0, 3.0),  # 3,5 bornée à 3
        (-2.0, 5.0, -3.0),  # −3,5 bornée à −3
    ],
)
def test_la_couleur_est_la_demi_difference_bornee(
    intensite: float, sensations: float, attendue: float
) -> None:
    assert couleur(intensite, sensations, PETITS) == pytest.approx(attendue, abs=TOLERANCE)


def test_la_borne_de_couleur_vient_des_parametres() -> None:
    assert couleur(2.0, -5.0, dataclasses.replace(PETITS, couleur_borne=2.5)) == 2.5


def test_une_participation_a_charge_nulle_n_est_pas_une_absence() -> None:
    # RPE 0 le jour D : charge 0, intensité (0 − 200) / 100 = −2. Entrée de D − 1 à 1 :
    # sensations (1 − 0,5) / 0,1 = 5. Couleur (−2 − 5) / 2 = −3,5, bornée à −3.
    participations = [*MONTEE[:3], ParticipationValidee(D, 100, 0, 0, 0)]
    forme = forme_actuelle(participations, [*REFERENCE, _entree(-1, 10)], [PLAISIR], PETITS, D)

    assert (forme.etat, forme.absent_depuis_jours) == (EtatForme.OK, None)
    assert forme.point is not None
    assert forme.point.intensite == pytest.approx(-2.0, abs=TOLERANCE)
    assert forme.point.sensations == pytest.approx(5.0, abs=TOLERANCE)
    assert forme.point.couleur == pytest.approx(-3.0, abs=TOLERANCE)


# --- Entrée de sensations retenue (ADR-0018, Q3) --------------------------------------


def test_l_entree_retenue_est_la_plus_recente_de_d_moins_3_a_d() -> None:
    assert entree_retenue([_z(-5), _z(-3), _z(-2)], PETITS, D) == _z(-2)
    assert entree_retenue([_z(0), _z(-1)], PETITS, D) == _z(0)  # D inclus, ordre indifférent
    assert entree_retenue([_z(-3), _z(1)], PETITS, D) == _z(-3)  # D − 3 inclus, D + 1 ignorée
    assert entree_retenue([_z(-4)], PETITS, D) is None  # D − 4 exclue
    assert entree_retenue([], PETITS, D) is None


def test_la_fraicheur_vient_des_parametres() -> None:
    quatre = dataclasses.replace(PETITS, fraicheur_entree_jours=4)
    assert entree_retenue([_z(-4)], quatre, D) == _z(-4)
    assert entree_retenue([_z(-5)], quatre, D) is None


def test_une_entree_sans_score_n_est_pas_remplacee_par_une_plus_ancienne() -> None:
    insuffisante = _z(-1, Etat.REPONSES_INSUFFISANTES)
    assert entree_retenue([_z(-2), insuffisante], PETITS, D) == insuffisante


def test_l_age_de_l_entree_retenue_est_compte_en_jours() -> None:
    # Entrée de D − 3 à 0,3, contre 0,4, 0,5, 0,6 décalées d'un jour : z = −2, âge 3.
    entrees = [_entree(-7, 4), _entree(-6, 5), _entree(-5, 6), _entree(-3, 3)]
    forme = forme_actuelle(MONTEE, entrees, [PLAISIR], PETITS, D)

    assert (forme.etat, forme.jour_entree, forme.age_entree_jours) == (
        EtatForme.OK,
        _jour(-3),
        3,
    )
    assert forme.point is not None
    assert forme.point.sensations == pytest.approx(-2.0, abs=TOLERANCE)


# --- États sans point (ADR-0018, Q4) ---------------------------------------------------


@pytest.mark.parametrize(
    ("participations", "etat"),
    [
        ([], EtatForme.HISTORIQUE_INSUFFISANT),  # aucune participation : pas de calendrier
        ([_seance(-1, 1), _seance(0, 2)], EtatForme.HISTORIQUE_INSUFFISANT),  # 1 jour < 2
        ([_seance(k, 1) for k in range(-3, 1)], EtatForme.NON_CALCULABLE),  # 100 × 3 : s = 0
    ],
)
def test_une_intensite_sans_z_score_ne_donne_pas_de_point(
    participations: list[ParticipationValidee], etat: EtatForme
) -> None:
    forme = forme_actuelle(participations, [*REFERENCE, _entree(-1, 3)], [PLAISIR], PETITS, D)

    assert (forme.etat, forme.point, forme.absent_depuis_jours) == (etat, None, None)
    # Les sensations restent calculées pour le tableau de valeurs.
    assert forme.sensations is not None and forme.sensations.etat is Etat.OK


@pytest.mark.parametrize(
    ("entrees", "etat"),
    [
        (REFERENCE, EtatForme.PAS_D_ENTREE_RECENTE),  # dernière entrée en D − 4
        ([_entree(-1, 3)], EtatForme.HISTORIQUE_INSUFFISANT),  # aucune entrée de référence
        (
            [_entree(-6, 5), _entree(-5, 5), _entree(-4, 5), _entree(-1, 3)],
            EtatForme.NON_CALCULABLE,  # référence 0,5 × 3 : s = 0
        ),
        # L'entrée de D − 1 n'a pas de score ; celle de D − 2 n'est pas reprise.
        ([*REFERENCE, _entree(-2, 3), _entree(-1, None)], EtatForme.REPONSES_INSUFFISANTES),
    ],
)
def test_des_sensations_sans_z_score_ne_donnent_pas_de_point(
    entrees: list[EntreeSensations], etat: EtatForme
) -> None:
    forme = forme_actuelle(MONTEE, entrees, [PLAISIR], PETITS, D)

    assert (forme.etat, forme.point, forme.absent_depuis_jours) == (etat, None, None)
    assert forme.intensite is not None and forme.intensite.etat is Etat.OK


def test_sans_entree_recente_ni_date_ni_age() -> None:
    forme = forme_actuelle(MONTEE, REFERENCE, [PLAISIR], PETITS, D)
    assert (forme.sensations, forme.jour_entree, forme.age_entree_jours) == (None, None, None)


def test_des_reponses_insuffisantes_gardent_la_date_de_l_entree() -> None:
    entrees = [*REFERENCE, _entree(-2, 3), _entree(-1, None)]
    forme = forme_actuelle(MONTEE, entrees, [PLAISIR], PETITS, D)
    assert (forme.jour_entree, forme.age_entree_jours) == (_jour(-1), 1)
    assert forme.sensations is not None
    assert forme.sensations.etat is Etat.REPONSES_INSUFFISANTES


def test_l_etat_de_l_intensite_passe_avant_l_absence_d_entree_recente() -> None:
    forme = forme_actuelle([], REFERENCE, [PLAISIR], PETITS, D)
    assert (forme.etat, forme.intensite, forme.sensations) == (
        EtatForme.HISTORIQUE_INSUFFISANT,
        None,
        None,
    )


# --- Absence (R14, ADR-0013) -----------------------------------------------------------


def test_un_joueur_sans_participation_sur_la_fenetre_courte_est_absent() -> None:
    # Fenêtre courte de 7 jours : une seule participation le jour D.
    # D + 6 : la participation est dans la fenêtre (D à D + 6), le joueur n'est pas absent ;
    # D + 7 : fenêtre D + 1 à D + 7 vide, absent depuis 7 jours.
    seule = [ParticipationValidee(D, 60, 5, 5, 5)]
    six = forme_actuelle(seule, [], [PLAISIR], STANDARD, _jour(6))
    sept = forme_actuelle(seule, [], [PLAISIR], STANDARD, _jour(7))

    assert (six.etat, six.absent_depuis_jours) == (EtatForme.HISTORIQUE_INSUFFISANT, None)
    assert (sept.etat, sept.absent_depuis_jours, sept.point) == (EtatForme.ABSENT, 7, None)
    assert absent_depuis(seule, STANDARD, _jour(6)) is None
    assert absent_depuis(seule, STANDARD, _jour(7)) == 7
    assert absent_depuis([], STANDARD, D) is None


def test_l_absence_passe_avant_une_intensite_calculable() -> None:
    # Charges 100, 200, 300 de D − 4 à D − 2, rien ensuite ; fenêtre courte de 1 jour :
    # absent depuis 2 jours. Intensité de D : CE 0 contre 200, 300, 0 ; m = 500/3,
    # s² = (100² + 400² + 500²) / 9 / 2 = 210000/9, z = −(500/3) / (√210000 / 3) = −5/√21.
    participations = [_seance(-4, 1), _seance(-3, 2), _seance(-2, 3)]
    forme = forme_actuelle(participations, [*REFERENCE, _entree(-1, 3)], [PLAISIR], PETITS, D)

    assert (forme.etat, forme.absent_depuis_jours, forme.point) == (EtatForme.ABSENT, 2, None)
    assert forme.intensite is not None and forme.intensite.valeur is not None
    assert forme.intensite.valeur == pytest.approx(-5 / math.sqrt(21), abs=TOLERANCE)


def _c4() -> tuple[list[ParticipationValidee], dict[tuple[datetime.date, str], float | None]]:
    cas = lire_cas(trouver_dossier("C04"))
    seances = {s.id: s for s in cas.seances}
    participations = []
    for p in cas.participations:
        s = seances[p.seance_id]
        assert p.rpe_cardio is not None and p.rpe_musculaire is not None
        assert p.rpe_teta is not None and s.statut == "validee"
        participations.append(
            ParticipationValidee(s.date, s.duree_min, p.rpe_cardio, p.rpe_musculaire, p.rpe_teta)
        )
    return participations, {(a.date, a.grandeur): a.valeur for a in cas.attendu}


@pytest.mark.parametrize(
    ("jour", "absent"),
    [
        (datetime.date(2026, 2, 12), None),  # dernière séance le 6 : dans la fenêtre du 6 au 12
        (datetime.date(2026, 2, 13), 7),  # fenêtre du 7 au 13 vide
        (datetime.date(2026, 2, 16), 10),  # dix jours d'absence, du 7 au 16
    ],
)
def test_c4_le_joueur_absent_sort_du_graphique_malgre_une_intensite_calculable(
    jour: datetime.date, absent: int | None
) -> None:
    participations, attendu = _c4()
    forme = forme_actuelle(participations, [], [], STANDARD, jour)

    # C04 n'a pas de sensations : sans absence, l'état est « pas d'entrée récente ».
    etat = EtatForme.ABSENT if absent is not None else EtatForme.PAS_D_ENTREE_RECENTE
    assert (forme.etat, forme.absent_depuis_jours, forme.point) == (etat, absent, None)
    # L'intensité du jour, valeur du mainteneur, aurait placé un point très à gauche.
    assert forme.intensite is not None and forme.intensite.etat is Etat.OK
    assert forme.intensite.valeur == pytest.approx(attendu[(jour, "intensite")], abs=1e-6)


# --- Date de calcul (C9) ---------------------------------------------------------------


def test_c9_les_donnees_posterieures_a_d_sont_ignorees() -> None:
    entrees = [*REFERENCE, _entree(-1, 3)]
    a_d = forme_actuelle(MONTEE, entrees, [PLAISIR], PETITS, D)
    avec_la_suite = forme_actuelle(
        [*MONTEE, _seance(1, 10)],
        [*entrees, _entree(1, 10), _entree(2, None)],
        [PLAISIR],
        PETITS,
        D,
    )
    assert avec_la_suite == a_d


def test_deux_entrees_le_meme_jour_sont_une_anomalie() -> None:
    with pytest.raises(ValueError, match="même jour"):
        forme_actuelle(MONTEE, [_entree(-1, 3), _entree(-1, 4)], [PLAISIR], PETITS, D)
