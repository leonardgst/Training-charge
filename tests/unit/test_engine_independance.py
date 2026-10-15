"""`engine/` n'importe jamais Django (ni l'application) : seule la bibliothèque standard."""

import ast
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
AUTORISES = set(sys.stdlib_module_names) | {"engine"}


def _modules_importes(fichier: Path) -> set[str]:
    modules: set[str] = set()
    for noeud in ast.walk(ast.parse(fichier.read_text(encoding="utf-8"))):
        if isinstance(noeud, ast.Import):
            modules |= {alias.name.split(".")[0] for alias in noeud.names}
        elif isinstance(noeud, ast.ImportFrom) and noeud.level == 0:
            modules.add((noeud.module or "").split(".")[0])
    return modules


def test_le_moteur_n_importe_que_la_bibliotheque_standard() -> None:
    fautes = {
        f"{fichier.relative_to(RACINE)} : {module}"
        for fichier in sorted((RACINE / "engine").rglob("*.py"))
        for module in _modules_importes(fichier) - AUTORISES
    }
    assert fautes == set()


def test_le_detecteur_voit_un_import_de_django(tmp_path: Path) -> None:
    fichier = tmp_path / "faute.py"
    fichier.write_text("from django.db import models\nimport suivi.models\n", encoding="utf-8")
    assert _modules_importes(fichier) == {"django", "suivi"}
