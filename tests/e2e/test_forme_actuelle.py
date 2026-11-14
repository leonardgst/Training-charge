"""Parcours « Forme actuelle » : le graphique s'affiche sans violation de la politique de
sécurité du contenu, aux trois formats, avec son tableau de valeurs (US-10, ADR-0018)."""

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


def test_le_graphique_s_affiche_sans_violation_et_avec_son_tableau(
    page_formatee: Page, live_server
) -> None:
    call_command("generer_demo", fin=aujourd_hui(), mot_de_passe=MOT_DE_PASSE, verbosity=0)
    violations: list[str] = []
    erreurs: list[str] = []

    def noter(message: ConsoleMessage) -> None:
        if "Content Security Policy" in message.text:
            violations.append(message.text)
        elif message.type == "error":
            erreurs.append(message.text)

    page = page_formatee
    page.on("console", noter)
    page.on("pageerror", lambda erreur: erreurs.append(str(erreur)))
    page.goto(live_server.url + "/connexion/")
    page.get_by_label("Nom d’utilisateur").fill("prep_u19")
    page.get_by_label("Mot de passe").fill(MOT_DE_PASSE)
    page.locator("form [type=submit]").last.click()
    page.get_by_role("link", name="Forme actuelle").click()

    expect(page.get_by_role("heading", name="Forme actuelle", level=1)).to_be_visible()
    expect(page.locator("#graphique-forme svg")).to_be_visible()
    assert page.locator("#graphique-forme svg path[role='graphics-symbol']").count() > 0
    expect(page.locator("#valeurs-forme")).to_be_visible()
    titres = page.locator("#graphique-forme svg .role-axis-title")
    expect(titres.filter(has_text="Sensations dégradées ↑")).to_have_count(1)
    expect(titres.filter(has_text="Intensité")).to_have_count(1)
    # Aucun débordement horizontal de la page.
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    assert violations == []
    assert erreurs == []


def test_l_infobulle_donne_le_joueur_et_la_date_de_l_entree(page: Page, live_server) -> None:
    call_command("generer_demo", fin=aujourd_hui(), mot_de_passe=MOT_DE_PASSE, verbosity=0)
    violations: list[str] = []
    page.on("pageerror", lambda erreur: violations.append(str(erreur)))
    page.on(
        "console",
        lambda m: violations.append(m.text) if "Content Security Policy" in m.text else None,
    )
    page.goto(live_server.url + "/connexion/")
    page.get_by_label("Nom d’utilisateur").fill("prep_u19")
    page.get_by_label("Mot de passe").fill(MOT_DE_PASSE)
    page.locator("form [type=submit]").last.click()
    page.goto(live_server.url + "/forme/")
    page.locator("#graphique-forme svg path[role='graphics-symbol']").first.hover()
    infobulle = page.locator("#vg-tooltip-element")
    expect(infobulle).to_be_visible()
    expect(infobulle).to_contain_text("Joueur")
    expect(infobulle).to_contain_text("Entrée du")
    assert violations == []
