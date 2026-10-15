"""En-têtes de sécurité sur toutes les réponses (architecture, section 5).

Politique de sécurité du contenu limitée à l'origine du site, `Referrer-Policy:
same-origin`, `X-Frame-Options: DENY`, quel que soit le type de réponse : page, redirection,
refus, erreur, administration, contrôle de santé.
"""

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from suivi.models import Categorie, Preparateur

pytestmark = pytest.mark.django_db

CHEMINS_ANONYMES = {
    "page de connexion": ("/connexion/", 200),
    "redirection vers la connexion": ("/", 302),
    "page introuvable": ("/n-existe-pas/", 404),
    "connexion de l'administration": ("/admin/login/", 200),
    "contrôle de santé": ("/sante/", 200),
}


def directives(en_tete: str) -> dict[str, list[str]]:
    """`default-src 'self'; img-src 'self' data:` -> {"default-src": ["'self'"], ...}."""
    resultat: dict[str, list[str]] = {}
    for morceau in en_tete.split(";"):
        nom, *sources = morceau.split()
        assert nom not in resultat, f"directive en double : {nom}"
        resultat[nom] = sources
    return resultat


def _verifier(reponse) -> None:  # noqa: ANN001
    politique = directives(reponse["Content-Security-Policy"])

    assert politique["default-src"] == ["'self'"]
    # Pico CSS dessine ses icônes en SVG intégrés : seule exception à l'origine du site.
    assert politique["img-src"] == ["'self'", "data:"]
    assert politique["object-src"] == ["'none'"]
    assert politique["base-uri"] == ["'none'"]
    assert politique["form-action"] == ["'self'"]
    assert politique["frame-ancestors"] == ["'none'"]
    # Scripts et styles retombent sur `default-src` : rien en ligne, rien d'ailleurs.
    for directive in ("script-src", "style-src", "connect-src", "font-src"):
        assert politique.get(directive, ["'self'"]) == ["'self'"], directive
    sources = {source for liste in politique.values() for source in liste}
    assert not sources & {"'unsafe-inline'", "'unsafe-eval'", "*", "http:", "https:"}


@pytest.mark.parametrize("cas", CHEMINS_ANONYMES)
def test_chaque_reponse_a_un_visiteur_porte_la_politique(client: Client, cas: str) -> None:
    chemin, statut = CHEMINS_ANONYMES[cas]

    reponse = client.get(chemin)

    assert reponse.status_code == statut
    _verifier(reponse)


@pytest.mark.parametrize("cas", CHEMINS_ANONYMES)
def test_aucune_reponse_ne_transmet_le_referent_a_un_autre_site_ni_ne_s_affiche_en_cadre(
    client: Client, cas: str
) -> None:
    reponse = client.get(CHEMINS_ANONYMES[cas][0])

    # `no-referrer` ferait envoyer `Origin: null` aux formulaires POST, refusé par le
    # contrôle CSRF de Django : `same-origin` ne transmet rien à un autre site.
    assert reponse["Referrer-Policy"] == "same-origin"
    assert reponse["X-Frame-Options"] == "DENY"


def test_les_pages_du_staff_portent_la_politique(client: Client) -> None:
    compte = get_user_model().objects.create_user("prep")
    Preparateur.objects.create(
        user=compte, categorie=Categorie.objects.create(code="U19", libelle="U19")
    )
    client.force_login(compte)

    reponse = client.get("/")

    assert reponse.status_code == 200
    _verifier(reponse)


def test_un_refus_porte_la_politique(client: Client) -> None:
    client.force_login(get_user_model().objects.create_user("sans_profil"))

    reponse = client.get("/")

    assert reponse.status_code == 403
    _verifier(reponse)


def test_l_administration_porte_la_politique(client: Client) -> None:
    client.force_login(get_user_model().objects.create_superuser("admin"))

    reponse = client.get("/admin/suivi/joueur/add/")

    assert reponse.status_code == 200
    _verifier(reponse)
