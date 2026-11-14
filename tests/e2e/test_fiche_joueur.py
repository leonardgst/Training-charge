"""Parcours fiche joueur : de la liste des joueurs à la charge, aux trois formats (US-11)."""

import secrets

import pytest
from django.core.management import call_command
from playwright.sync_api import ConsoleMessage, Page, ViewportSize, expect

from suivi.horloge import aujourd_hui

pytestmark = pytest.mark.django_db(transaction=True)

MOT_DE_PASSE = secrets.token_urlsafe(12)

FORMATS: dict[str, ViewportSize] = {
    "ordinateur": {"width": 1280, "height": 800},
    "tablette": {"width": 820, "height": 1180},
    "telephone": {"width": 390, "height": 844},
}


@pytest.fixture(params=sorted(FORMATS))
def page_formatee(page: Page, request: pytest.FixtureRequest) -> Page:
    page.set_viewport_size(FORMATS[request.param])
    return page


def test_la_fiche_s_ouvre_depuis_les_joueurs_avec_ses_rpe_et_ses_barres(
    page_formatee: Page, live_server
) -> None:
    call_command("generer_demo", fin=aujourd_hui(), mot_de_passe=MOT_DE_PASSE, verbosity=0)
    problemes: list[str] = []

    def noter(message: ConsoleMessage) -> None:
        if "Content Security Policy" in message.text or message.type == "error":
            problemes.append(message.text)

    page = page_formatee
    page.on("console", noter)
    page.on("pageerror", lambda erreur: problemes.append(str(erreur)))
    page.goto(live_server.url + "/connexion/")
    page.get_by_label("Nom d’utilisateur").fill("prep_u19")
    page.get_by_label("Mot de passe").fill(MOT_DE_PASSE)
    page.locator("form [type=submit]").last.click()
    page.goto(live_server.url + "/joueurs/")
    page.get_by_role("link", name="Fiche de").first.click()

    expect(page.get_by_role("heading", name="Fiche de", level=1)).to_be_visible()
    expect(page.locator("#rpe-seances")).to_be_visible()
    assert page.locator("#rpe-seances span.rpe[data-niveau]").count() > 0
    expect(page.locator("#graphique-forme svg")).to_be_visible()
    assert page.locator("#graphique-forme svg path[role='graphics-symbol']").count() > 0
    expect(page.locator("#valeurs-charge")).to_be_visible()
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    assert problemes == []
