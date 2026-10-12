"""Aucun document ne cite un fichier qui n'existe pas (cadrage 10.4).

Seule l'existence du fichier cible est vérifiée, pas celle de l'ancre qui le suit.
"""

import re
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[2]

BLOCS_DE_CODE = re.compile(r"^(```|~~~).*?^\1[ \t]*$", re.MULTILINE | re.DOTALL)
CODE_EN_LIGNE = re.compile(r"`[^`\n]*`")
LIEN = re.compile(r"!?\[[^\]\n]*\]\(<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\)")
SCHEMAS_EXTERNES = ("http://", "https://", "mailto:", "tel:")


def liens_casses(texte: str, dossier: Path) -> list[str]:
    """Cibles relatives de `texte` qui ne désignent aucun fichier ou dossier existant."""
    texte = BLOCS_DE_CODE.sub("", texte)
    texte = CODE_EN_LIGNE.sub("", texte)
    casses = []
    for cible in LIEN.findall(texte):
        if cible.startswith(SCHEMAS_EXTERNES) or cible.startswith("#"):
            continue
        chemin = cible.split("#", 1)[0].split("?", 1)[0]
        base = RACINE if chemin.startswith("/") else dossier
        if not (base / chemin.lstrip("/")).exists():
            casses.append(cible)
    return casses


def documents() -> list[Path]:
    fichiers = sorted((RACINE / "docs").rglob("*.md"))
    fichiers += [RACINE / nom for nom in ("README.md", "CLAUDE.md") if (RACINE / nom).exists()]
    return fichiers


@pytest.mark.parametrize("document", documents(), ids=lambda p: p.relative_to(RACINE).as_posix())
def test_les_liens_relatifs_d_un_document_existent(document: Path) -> None:
    texte = document.read_text(encoding="utf-8")

    assert liens_casses(texte, document.parent) == []


def test_le_controle_detecte_un_lien_casse(tmp_path: Path) -> None:
    (tmp_path / "present.md").write_text("cible", encoding="utf-8")
    texte = "\n".join(
        [
            "[ok](present.md) [ok avec ancre](present.md#section)",
            "[externe](https://exemple.org/absent.md) [ancre seule](#haut)",
            "[cassé](absent.md) [cassé avec ancre](absent.md#section)",
            "`[en ligne](ignore-1.md)`",
            "```",
            "[dans un bloc](ignore-2.md)",
            "```",
        ]
    )

    assert liens_casses(texte, tmp_path) == ["absent.md", "absent.md#section"]
