"""Les vues ne contournent pas `suivi/acces.py` (ADR-0005, couche 4)."""

import re
from pathlib import Path

VUES = Path(__file__).resolve().parents[2] / "suivi" / "views"


def test_aucune_vue_n_interroge_directement_un_modele() -> None:
    fautives = [
        f"{fichier.name}:{numero}"
        for fichier in sorted(VUES.glob("*.py"))
        for numero, ligne in enumerate(fichier.read_text().splitlines(), start=1)
        if re.search(r"\.objects\b|\.get_object_or_404|get_list_or_404", ligne)
    ]
    assert fautives == []
