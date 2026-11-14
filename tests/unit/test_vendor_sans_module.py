"""Les scripts copiés dans `vendor/` sont chargés comme scripts classiques (ADR-0020) : aucun
module ES (`import` ou `export` de tête), qui lèverait une erreur de syntaxe au chargement."""

import re
from pathlib import Path

import pytest

VENDOR = Path(__file__).resolve().parent.parent.parent / "suivi" / "static" / "suivi" / "vendor"
MODULE = re.compile(r"(?:^|[;}\n])\s*(?:import\s*[{*\w]|export\s*[{*\w])")
SCRIPTS = sorted(VENDOR.rglob("*.js"))


def test_il_y_a_des_scripts_a_controler() -> None:
    assert SCRIPTS


@pytest.mark.parametrize("script", SCRIPTS, ids=lambda p: p.name)
def test_un_script_copie_n_est_pas_un_module_es(script: Path) -> None:
    texte = script.read_text(encoding="utf-8")
    sans_commentaire = re.sub(r"/\*.*?\*/", "", texte, count=1, flags=re.S)
    assert not sans_commentaire.lstrip().startswith(("import", "export"))
    assert "export{" not in sans_commentaire[-400:]
    assert "sourceMappingURL=/" not in texte
