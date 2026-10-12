"""Parcours de connexion dans un vrai navigateur, sur ordinateur et sur téléphone."""

import pytest
from playwright.sync_api import Page, ViewportSize, expect

pytestmark = pytest.mark.django_db(transaction=True)

FORMATS: dict[str, ViewportSize] = {
    "ordinateur": {"width": 1280, "height": 800},
    "telephone": {"width": 390, "height": 844},
}


@pytest.fixture(params=sorted(FORMATS))
def page_formatee(page: Page, request: pytest.FixtureRequest) -> Page:
    page.set_viewport_size(FORMATS[request.param])
    return page


def test_la_racine_mene_a_la_connexion(page_formatee: Page, live_server) -> None:
    page_formatee.goto(live_server.url + "/")

    expect(page_formatee).to_have_url(live_server.url + "/connexion/?next=/")
    expect(page_formatee.get_by_role("heading", name="Connexion")).to_be_visible()


def test_la_connexion_aboutit_a_l_accueil(
    page_formatee: Page, live_server, django_user_model
) -> None:
    django_user_model.objects.create_user("preparateur", password="mot-de-passe-de-test-1")  # noqa: S106

    page_formatee.goto(live_server.url + "/connexion/")
    page_formatee.get_by_label("Nom d’utilisateur").fill("preparateur")
    page_formatee.get_by_label("Mot de passe").fill("mot-de-passe-de-test-1")
    page_formatee.get_by_role("button", name="Se connecter").click()

    expect(page_formatee).to_have_url(live_server.url + "/")
    expect(page_formatee.get_by_role("button", name="Se connecter")).to_have_count(0)


def test_un_mauvais_mot_de_passe_reste_sur_la_connexion(page_formatee: Page, live_server) -> None:
    page_formatee.goto(live_server.url + "/connexion/")
    page_formatee.get_by_label("Nom d’utilisateur").fill("inconnu")
    page_formatee.get_by_label("Mot de passe").fill("faux")
    page_formatee.get_by_role("button", name="Se connecter").click()

    expect(page_formatee).to_have_url(live_server.url + "/connexion/")
    expect(page_formatee.get_by_role("button", name="Se connecter")).to_be_visible()
