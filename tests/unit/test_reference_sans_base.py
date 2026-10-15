"""Cas C1 à C15 sans base : le moteur est appelé directement sur les données du cas.

Retour rapide en local ; la version sur base (tests/integration) fait foi. Chaque cas est
en `xfail(strict=True)` jusqu'à la PR de la phase 3 qui l'implémente (tests/reference/registre.py).
"""

import pytest

from tests.reference.execution import executer_sans_base
from tests.reference.harnais import (
    Cle,
    Resultat,
    comparer,
    lire_cas,
    trouver_dossier,
    verifier_coherence,
)
from tests.reference.registre import parametres_des_cas


@pytest.mark.parametrize("cas_id", parametres_des_cas(sans_base=True))
def test_cas_de_reference_sans_base(cas_id: str) -> None:
    cas = lire_cas(trouver_dossier(cas_id))
    verifier_coherence(cas)
    assert cas.attendu, f"{cas.nom} : attendu.csv est vide"
    obtenu: dict[Cle, Resultat] = {}
    for date_calcul in cas.dates_calcul:
        obtenu.update(executer_sans_base(cas, date_calcul))
    assert comparer(cas.attendu, obtenu) == []
