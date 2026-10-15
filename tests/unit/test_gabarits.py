"""Gabarits : ressources locales seulement, fichiers statiques présents, page 500 autonome."""

import re
from pathlib import Path

import pytest
from django.contrib.staticfiles import finders
from django.template.loader import render_to_string

GABARITS = sorted((Path(__file__).resolve().parents[2] / "suivi" / "templates").rglob("*.html"))
STATIQUE = re.compile(r"""{%\s*static\s+['"]([^'"]+)['"]\s*%}""")
RESSOURCE_EXTERNE = re.compile(r"""(?:src|href|action)\s*=\s*["']?\s*(?:[a-z]+:)?//""", re.I)


def test_les_gabarits_sont_trouves() -> None:
    noms = {gabarit.name for gabarit in GABARITS}
    assert {"base.html", "403.html", "404.html", "500.html"} <= noms


@pytest.mark.parametrize("gabarit", GABARITS, ids=lambda g: g.name)
def test_chaque_fichier_statique_cite_existe(gabarit: Path) -> None:
    for chemin in STATIQUE.findall(gabarit.read_text(encoding="utf-8")):
        assert finders.find(chemin) is not None, chemin


@pytest.mark.parametrize("gabarit", GABARITS, ids=lambda g: g.name)
def test_aucune_ressource_n_est_chargee_depuis_un_autre_site(gabarit: Path) -> None:
    assert RESSOURCE_EXTERNE.findall(gabarit.read_text(encoding="utf-8")) == []


def test_la_feuille_pico_est_accompagnee_de_sa_licence() -> None:
    feuille = finders.find("suivi/vendor/pico/pico.min.css")
    licence = finders.find("suivi/vendor/pico/LICENSE.md")

    assert feuille is not None and licence is not None
    assert "Pico CSS ✨ v2.1.1" in Path(feuille).read_text(encoding="utf-8")[:200]
    assert "MIT License" in Path(licence).read_text(encoding="utf-8")


def test_la_page_500_se_rend_sans_requete_ni_contexte() -> None:
    # `django.views.defaults.server_error` rend ce gabarit sans contexte ni requête.
    page = render_to_string("500.html")

    assert '<html lang="fr">' in page
    assert "<h1>Erreur</h1>" in page
    assert "Se déconnecter" not in page
