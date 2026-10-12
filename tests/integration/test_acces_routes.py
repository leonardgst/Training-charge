"""Visiteur non connecté face au catalogue des routes (A1, squelette).

Toutes les routes du résolveur d'URL sont parcourues en GET et en POST, sans session :
chacune doit rediriger vers la connexion ou refuser, sauf la liste blanche.
"""

import re

import pytest
from django.test import Client
from django.urls import URLPattern, URLResolver, get_resolver

# Routes publiques voulues (ADR-0005) : connexion, contrôle de santé, connexion de l'admin.
LISTE_BLANCHE = {"/connexion/", "/sante/", "/admin/login/"}


def _routes(motifs: list, prefixe: str = "") -> list[str]:
    chemins: list[str] = []
    for motif in motifs:
        if isinstance(motif, URLResolver):
            chemins += _routes(motif.url_patterns, prefixe + str(motif.pattern))
        elif isinstance(motif, URLPattern):
            chemins.append(prefixe + str(motif.pattern))
    return chemins


def _chemin_concret(motif: str) -> str:
    """Remplace chaque paramètre du motif par une valeur plausible."""
    chemin = re.sub(r"<(?:int:)?[^>]*(?:id|pk|object_id)>", "1", motif)
    chemin = re.sub(r"<[^>]+>", "x", chemin)
    return "/" + chemin.removeprefix("^").removesuffix("$")


CHEMINS = sorted({_chemin_concret(m) for m in _routes(get_resolver().url_patterns)})


def test_le_catalogue_contient_les_routes_connues() -> None:
    assert {"/", "/connexion/", "/sante/"} <= set(CHEMINS)


@pytest.mark.parametrize("methode", ["get", "post"])
@pytest.mark.parametrize("chemin", [c for c in CHEMINS if c not in LISTE_BLANCHE])
def test_une_route_hors_liste_blanche_ne_donne_rien_a_un_visiteur(
    chemin: str, methode: str
) -> None:
    reponse = getattr(Client(), methode)(chemin)

    assert reponse.status_code in {301, 302, 401, 403, 404}
    if reponse.status_code in {301, 302}:
        assert "/login/" in reponse["Location"] or "/connexion/" in reponse["Location"]
