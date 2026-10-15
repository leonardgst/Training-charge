"""Parcours de connexion dans un vrai navigateur, sur ordinateur, tablette et téléphone."""

import pytest
from playwright.sync_api import Page, ViewportSize, expect

from suivi.models import Categorie, Preparateur

pytestmark = pytest.mark.django_db(transaction=True)

FORMATS: dict[str, ViewportSize] = {
    "ordinateur": {"width": 1280, "height": 800},
    "tablette": {"width": 820, "height": 1180},
    "telephone": {"width": 390, "height": 844},
}


@pytest.fixture(params=sorted(FORMATS))
def page_formatee(page: Page, request: pytest.FixtureRequest) -> Page:
    page.set_viewport_size(FORMATS[request.param])
    return page


@pytest.fixture
def preparateur(django_user_model) -> None:
    compte = django_user_model.objects.create_user(
        "preparateur",
        password="mot-de-passe-de-test-1",  # noqa: S106
    )
    Preparateur.objects.create(
        user=compte, categorie=Categorie.objects.create(code="U19", libelle="U19")
    )


def _se_connecter(page: Page, url: str) -> None:
    page.goto(url + "/connexion/")
    page.get_by_label("Nom d’utilisateur").fill("preparateur")
    page.get_by_label("Mot de passe").fill("mot-de-passe-de-test-1")
    page.get_by_role("button", name="Se connecter").click()


def _sans_debordement_horizontal(page: Page) -> bool:
    return page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")


def test_la_racine_mene_a_la_connexion(page_formatee: Page, live_server) -> None:
    page_formatee.goto(live_server.url + "/")

    expect(page_formatee).to_have_url(live_server.url + "/connexion/?next=/")
    expect(page_formatee.get_by_role("heading", name="Connexion")).to_be_visible()


def test_la_connexion_aboutit_a_l_accueil(
    page_formatee: Page, live_server, preparateur: None
) -> None:
    _se_connecter(page_formatee, live_server.url)

    expect(page_formatee).to_have_url(live_server.url + "/")
    expect(page_formatee.get_by_role("heading", name="Suivi de charge U19")).to_be_visible()


def test_un_mauvais_mot_de_passe_reste_sur_la_connexion(page_formatee: Page, live_server) -> None:
    page_formatee.goto(live_server.url + "/connexion/")
    page_formatee.get_by_label("Nom d’utilisateur").fill("inconnu")
    page_formatee.get_by_label("Mot de passe").fill("faux")
    page_formatee.get_by_role("button", name="Se connecter").click()

    expect(page_formatee).to_have_url(live_server.url + "/connexion/")
    expect(page_formatee.get_by_role("button", name="Se connecter")).to_be_visible()
    expect(page_formatee.get_by_role("alert")).to_contain_text("nom d’utilisateur")
    expect(page_formatee.get_by_role("alert")).to_contain_text("mot de passe")


def test_la_deconnexion_ramene_a_la_connexion(
    page_formatee: Page, live_server, preparateur: None
) -> None:
    _se_connecter(page_formatee, live_server.url)
    page_formatee.get_by_role("button", name="Se déconnecter").click()

    expect(page_formatee).to_have_url(live_server.url + "/connexion/")
    page_formatee.goto(live_server.url + "/")
    expect(page_formatee).to_have_url(live_server.url + "/connexion/?next=/")


def test_les_pages_tiennent_dans_la_largeur_de_l_ecran(
    page_formatee: Page, live_server, preparateur: None
) -> None:
    page_formatee.goto(live_server.url + "/connexion/")
    # La navigation passe à la ligne : preuve que Pico et la feuille du projet sont chargés.
    expect(page_formatee.locator("nav")).to_have_css("flex-wrap", "wrap")
    assert _sans_debordement_horizontal(page_formatee)

    _se_connecter(page_formatee, live_server.url)

    navigation = page_formatee.get_by_role("navigation", name="Navigation principale")
    expect(navigation.get_by_text("preparateur · U19")).to_be_in_viewport()
    expect(navigation.get_by_role("button", name="Se déconnecter")).to_be_in_viewport()
    assert _sans_debordement_horizontal(page_formatee)
