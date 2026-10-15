"""Cas C1 à C15 sur un vrai Postgres : l'adaptateur puis le moteur (cette version fait foi).

Le chargement du cas dans la base est testé ici avec le cas fictif du harnais ; les cas
de référence sont en `xfail(strict=True)` jusqu'à la PR qui les implémente.
"""

import datetime
from pathlib import Path

import pytest

from suivi.models import EntreeSensations, Joueur, Participation, Reponse, Seance
from tests.reference.execution import charger_en_base, executer_sur_base
from tests.reference.harnais import (
    Cle,
    Resultat,
    comparer,
    lire_cas,
    trouver_dossier,
    verifier_coherence,
)
from tests.reference.registre import parametres_des_cas
from tests.reference.synthese import ecrire_cas

pytestmark = pytest.mark.django_db(transaction=True)


def test_chargement_du_cas_fictif(tmp_path: Path) -> None:
    cas = lire_cas(ecrire_cas(tmp_path / "C00-test"))
    joueurs = charger_en_base(cas)

    assert set(joueurs) == {"J1", "J2"}
    assert Joueur.objects.count() == 2
    assert dict(Seance.objects.values_list("date", "statut")) == {
        datetime.date(2026, 1, 5): "validee",
        datetime.date(2026, 1, 6): "brouillon",
    }
    assert Participation.objects.count() == 3
    assert EntreeSensations.objects.count() == 1
    assert Reponse.objects.get().valeur == 3


def test_une_seance_validee_incomplete_est_refusee_par_la_base(tmp_path: Path) -> None:
    incomplete = "seance_id,joueur,rpe_cardio,rpe_musculaire,rpe_teta\nS1,J1,5,,4\nS1,J2,7,7,7\n"
    cas = lire_cas(ecrire_cas(tmp_path / "C00-test", **{"participations.csv": incomplete}))
    with pytest.raises(Exception, match="participations incomplètes"):
        charger_en_base(cas)


@pytest.mark.parametrize("cas_id", parametres_des_cas())
def test_cas_de_reference_sur_base(cas_id: str) -> None:
    cas = lire_cas(trouver_dossier(cas_id))
    verifier_coherence(cas)
    assert cas.attendu, f"{cas.nom} : attendu.csv est vide"
    joueurs = charger_en_base(cas)
    obtenu: dict[Cle, Resultat] = {}
    for date_calcul in cas.dates_calcul:
        obtenu.update(executer_sur_base(cas, joueurs, date_calcul))
    assert comparer(cas.attendu, obtenu) == []
