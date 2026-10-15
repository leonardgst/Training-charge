"""La politique de sécurité du contenu ne bloque rien sur les pages de l'application.

Chromium signale chaque violation par un message de console « Content Security Policy » :
aucune ne doit apparaître sur les pages du staff, ni dans l'administration (formulaire
d'un joueur, avec son widget de date). Le dernier test prouve que la détection fonctionne.
"""

import pytest
from playwright.sync_api import ConsoleMessage, Page, expect

from suivi.models import Categorie, Preparateur

pytestmark = pytest.mark.django_db(transaction=True)

MOT_DE_PASSE = "mot-de-passe-de-test-1"  # noqa: S105


def _ecouter_les_violations(page: Page) -> list[str]:
    violations: list[str] = []

    def noter(message: ConsoleMessage) -> None:
        if "Content Security Policy" in message.text:
            violations.append(message.text)

    page.on("console", noter)
    return violations


def _se_connecter(page: Page, url: str, nom: str) -> None:
    page.goto(url)
    page.get_by_label("Nom d’utilisateur").fill(nom)
    page.get_by_label("Mot de passe").fill(MOT_DE_PASSE)
    page.locator("form [type=submit]").last.click()


@pytest.fixture
def comptes(django_user_model) -> None:
    u19 = Categorie.objects.create(code="U19", libelle="U19")
    preparateur = django_user_model.objects.create_user("preparateur", password=MOT_DE_PASSE)
    Preparateur.objects.create(user=preparateur, categorie=u19)
    django_user_model.objects.create_superuser("admin", password=MOT_DE_PASSE)


def test_les_pages_du_staff_ne_declenchent_aucune_violation(
    page: Page, live_server, comptes: None
) -> None:
    violations = _ecouter_les_violations(page)

    _se_connecter(page, live_server.url + "/connexion/", "preparateur")
    expect(page.get_by_role("heading", name="Suivi de charge U19")).to_be_visible()
    page.goto(live_server.url + "/n-existe-pas/")
    expect(page.get_by_role("heading", name="Page introuvable")).to_be_visible()

    assert violations == []


def test_l_administration_ne_declenche_aucune_violation(
    page: Page, live_server, comptes: None
) -> None:
    violations = _ecouter_les_violations(page)

    _se_connecter(page, live_server.url + "/admin/login/", "admin")
    page.goto(live_server.url + "/admin/suivi/joueur/add/")
    # Raccourci « Aujourd'hui » du widget de date, inséré par le JavaScript de l'administration.
    page.locator(".datetimeshortcuts a").first.click()

    assert page.locator("#id_date_naissance").input_value() != ""
    assert violations == []


def test_un_style_en_ligne_serait_detecte(page: Page, live_server, comptes: None) -> None:
    violations = _ecouter_les_violations(page)
    page.goto(live_server.url + "/connexion/")

    page.evaluate("document.body.insertAdjacentHTML('beforeend', '<p style=\"color: red\">x</p>')")
    page.wait_for_timeout(200)

    assert violations != []
