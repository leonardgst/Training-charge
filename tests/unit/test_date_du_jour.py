"""La date du jour s'obtient par la fonction unique du projet (CLAUDE.md, section 5)."""

import datetime
import re
from pathlib import Path

from suivi.horloge import aujourd_hui

RACINE = Path(__file__).resolve().parents[2]
INTERDIT = re.compile(
    r"\b(?:date|datetime)\.today\(|datetime\.now\(|timezone\.now\(\)\.date|localdate\("
)


def test_aucun_module_ne_lit_la_date_du_jour_hors_de_horloge() -> None:
    fautives = [
        f"{fichier.relative_to(RACINE)}:{numero}"
        for dossier in ("suivi", "config", "engine")
        for fichier in sorted((RACINE / dossier).rglob("*.py"))
        if fichier.name != "horloge.py"
        for numero, ligne in enumerate(fichier.read_text().splitlines(), start=1)
        if INTERDIT.search(ligne)
    ]
    assert fautives == []


def test_aujourd_hui_renvoie_une_date_sans_heure() -> None:
    jour = aujourd_hui()
    assert type(jour) is datetime.date
