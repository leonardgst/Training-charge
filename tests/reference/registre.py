"""Registre des cas C1 à C15 du jeu de référence."""

import pytest

CAS = tuple(f"C{numero:02d}" for numero in range(1, 16))
# Cas d'intégration seulement (table de la section 8 de la stratégie de tests) : ils
# vérifient ce que fait l'adaptateur (brouillons, date de rétrospection, catégories,
# configuration en cours de saison) et ne tournent pas sans base.
INTEGRATION_SEULE = frozenset({"C05", "C09", "C10", "C15"})


def parametres_des_cas(*, sans_base: bool = False) -> list[object]:
    return [
        pytest.param(cas, id=cas) for cas in CAS if not (sans_base and cas in INTEGRATION_SEULE)
    ]
