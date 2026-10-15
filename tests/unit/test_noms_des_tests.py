"""Deux fichiers de test ne portent jamais le même nom.

Les dossiers de `tests/` n'ont pas de `__init__.py` : pytest importe chaque fichier sous son
seul nom, et refuse de collecter ensemble `tests/e2e/test_x.py` et
`tests/integration/test_x.py`. La CI lance les niveaux séparément et ne le verrait pas.
"""

from collections import Counter
from pathlib import Path

TESTS = Path(__file__).resolve().parents[1]


def test_aucun_nom_de_fichier_de_test_n_est_en_double() -> None:
    noms = Counter(fichier.name for fichier in TESTS.rglob("test_*.py"))

    assert [nom for nom, nombre in noms.items() if nombre > 1] == []
