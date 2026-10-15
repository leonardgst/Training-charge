"""Format et provenance du jeu de référence, et complétude du jeu du mainteneur."""

import ast
from pathlib import Path

from tests.reference.harnais import RACINE, CasAbsent, lire_cas, trouver_dossier, verifier_coherence
from tests.reference.registre import CAS

PREFIXES_INTERDITS = ("engine", "suivi")


def _dossiers_presents() -> list[Path]:
    return sorted(chemin for chemin in RACINE.glob("C[0-9][0-9]-*") if chemin.is_dir())


def test_les_dossiers_presents_respectent_le_format() -> None:
    for dossier in _dossiers_presents():
        cas = lire_cas(dossier)
        verifier_coherence(cas)
        assert cas.attendu, f"{dossier.name} : attendu.csv absent ou vide"
        provenance = dossier / "provenance.md"
        assert provenance.exists(), f"{dossier.name} : provenance.md absent"
        assert provenance.read_text(encoding="utf-8").strip(), (
            f"{dossier.name} : provenance.md vide"
        )


def test_les_outils_du_mainteneur_n_importent_ni_le_moteur_ni_l_application() -> None:
    fautes = []
    for script in sorted((RACINE / "outils").rglob("*.py")):
        for noeud in ast.walk(ast.parse(script.read_text(encoding="utf-8"))):
            noms = (
                [alias.name for alias in noeud.names]
                if isinstance(noeud, ast.Import)
                else [noeud.module or ""]
                if isinstance(noeud, ast.ImportFrom)
                else []
            )
            fautes += [
                f"{script.name} importe {nom}"
                for nom in noms
                if nom.split(".")[0] in PREFIXES_INTERDITS
            ]
    assert fautes == []


def test_le_jeu_de_reference_est_complet() -> None:
    manquants = []
    for cas in CAS:
        try:
            dossier = trouver_dossier(cas)
        except CasAbsent:
            manquants.append(cas)
            continue
        manquants += [
            f"{dossier.name}/{nom}"
            for nom in ("attendu.csv", "provenance.md")
            if not (dossier / nom).exists()
        ]
    assert manquants == []
