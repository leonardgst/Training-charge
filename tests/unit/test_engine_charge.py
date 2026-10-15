"""Charge de séance et calendrier continu du moteur (C1, C2 sans base).

Les valeurs attendues sont calculées à la main depuis l'ADR-0007 : (cardio + musculaire +
TETA) / 3 × durée × facteur.
"""

import datetime
import math

from engine.charge import calendrier, charge_seance
from engine.modeles import JourCalcule, Parametres, ParticipationValidee

PARAMETRES = Parametres(10, 7, 28, 28, 21, 1e-9)
LUNDI = datetime.date(2026, 1, 5)


def _participation(jour: datetime.date, duree: int, *rpe: int) -> ParticipationValidee:
    return ParticipationValidee(jour, duree, *rpe)


def test_charge_d_une_seance() -> None:
    # (5 + 6 + 4) / 3 = 5 ; 5 × 60 × 10 = 3000
    assert math.isclose(charge_seance(_participation(LUNDI, 60, 5, 6, 4), PARAMETRES), 3000.0)


def test_le_facteur_d_echelle_multiplie_la_charge() -> None:
    sept = Parametres(70, 7, 28, 28, 21, 1e-9)
    assert math.isclose(charge_seance(_participation(LUNDI, 60, 5, 6, 4), sept), 21000.0)


def test_une_seance_a_rpe_nuls_a_une_charge_nulle() -> None:
    assert charge_seance(_participation(LUNDI, 90, 0, 0, 0), PARAMETRES) == 0.0


def test_calendrier_continu_avec_jours_sans_seance_a_zero() -> None:
    jeudi = LUNDI + datetime.timedelta(days=3)
    participations = [_participation(LUNDI, 60, 5, 6, 4), _participation(jeudi, 45, 7, 7, 7)]
    jours = calendrier(participations, PARAMETRES, fin=LUNDI + datetime.timedelta(days=5))
    assert [j.jour for j in jours] == [LUNDI + datetime.timedelta(days=i) for i in range(6)]
    assert [round(j.charge_jour) for j in jours] == [3000, 0, 0, 3150, 0, 0]


def test_deux_seances_le_meme_jour_donnent_une_seule_ligne_additionnee() -> None:
    participations = [_participation(LUNDI, 60, 5, 6, 4), _participation(LUNDI, 45, 7, 7, 7)]
    assert calendrier(participations, PARAMETRES, fin=LUNDI) == [
        JourCalcule(LUNDI, charge_jour=6150.0)
    ]


def test_le_calendrier_commence_a_la_premiere_participation() -> None:
    mercredi = LUNDI + datetime.timedelta(days=2)
    jours = calendrier([_participation(mercredi, 60, 5, 5, 5)], PARAMETRES, fin=mercredi)
    assert [j.jour for j in jours] == [mercredi]


def test_les_participations_apres_la_date_de_calcul_sont_ignorees() -> None:
    apres = LUNDI + datetime.timedelta(days=1)
    participations = [_participation(LUNDI, 60, 5, 6, 4), _participation(apres, 60, 9, 9, 9)]
    assert calendrier(participations, PARAMETRES, fin=LUNDI) == [JourCalcule(LUNDI, 3000.0)]


def test_sans_participation_avant_la_date_de_calcul_le_calendrier_est_vide() -> None:
    assert calendrier([], PARAMETRES, fin=LUNDI) == []
    apres = [_participation(LUNDI + datetime.timedelta(days=1), 60, 5, 5, 5)]
    assert calendrier(apres, PARAMETRES, fin=LUNDI) == []
