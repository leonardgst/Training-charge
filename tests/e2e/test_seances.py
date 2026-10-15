"""Création d'une séance dans un vrai navigateur, sur ordinateur, tablette et téléphone (US-03)."""

import datetime

import pytest
from playwright.sync_api import Page, ViewportSize, expect

from suivi.models import Categorie, Joueur, Participation, Preparateur, Seance

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
def groupe(django_user_model) -> None:
    compte = django_user_model.objects.create_user(
        "preparateur",
        password="mot-de-passe-de-test-1",  # noqa: S106
    )
    u19 = Categorie.objects.create(code="U19", libelle="U19")
    u17 = Categorie.objects.create(code="U17", libelle="U17")
    Preparateur.objects.create(user=compte, categorie=u19)
    naissance = datetime.date(2007, 3, 14)
    for nom, prenom in [("Abel", "Yanis"), ("Bernard", "Léo"), ("Dupont", "Hugo")]:
        Joueur.objects.create(
            nom=nom, prenom=prenom, date_naissance=naissance, categorie_reference=u19
        )
    Joueur.objects.create(
        nom="Leroy", prenom="Noah", date_naissance=naissance, categorie_reference=u17
    )


def _se_connecter(page: Page, url: str) -> None:
    page.goto(url + "/connexion/")
    page.get_by_label("Nom d’utilisateur").fill("preparateur")
    page.get_by_label("Mot de passe").fill("mot-de-passe-de-test-1")
    page.get_by_role("button", name="Se connecter").click()


def _sans_debordement(page: Page) -> bool:
    return page.evaluate(
        "document.documentElement.scrollWidth <= window.innerWidth && "
        "[...document.querySelectorAll('.overflow-auto')]"
        ".every(zone => zone.scrollWidth <= zone.clientWidth)"
    )


def test_creer_une_seance_retirer_un_absent_et_ajouter_un_invite(
    page_formatee: Page, live_server, groupe: None
) -> None:
    page = page_formatee
    _se_connecter(page, live_server.url)
    page.get_by_role("link", name="Nouvelle séance").click()

    page.get_by_label("Date").fill("2026-10-14")
    page.get_by_label("Type").select_option("Musculation")
    page.get_by_label("Durée (minutes)").fill("75")
    expect(page.get_by_role("checkbox")).to_have_count(3)
    page.get_by_role("checkbox", name="Bernard Léo").uncheck()
    assert _sans_debordement(page)
    page.get_by_role("button", name="Créer la séance").click()

    expect(page.get_by_role("heading", name="Séance du mercredi 14 octobre 2026")).to_be_visible()
    expect(page.get_by_text("Musculation · 75 min · Brouillon")).to_be_visible()
    expect(page.get_by_role("heading", name="Participants (2)")).to_be_visible()

    page.get_by_role("searchbox", name="Nom ou prénom du joueur").fill("ler")
    page.get_by_role("button", name="Rechercher").click()
    page.get_by_role("button", name="Ajouter Noah Leroy").click()
    expect(page.get_by_role("status")).to_have_text("Noah Leroy est ajouté à la séance.")
    expect(page.get_by_role("heading", name="Participants (3)")).to_be_visible()
    expect(page.get_by_role("cell", name="U17")).to_be_visible()

    page.get_by_role("button", name="Retirer Hugo Dupont").click()
    expect(page.get_by_role("status")).to_have_text("Hugo Dupont est retiré de la séance.")
    assert _sans_debordement(page)

    seance = Seance.objects.get()
    assert (seance.date, seance.type, seance.duree_min) == (
        datetime.date(2026, 10, 14),
        "musculation",
        75,
    )
    noms = {p.joueur.nom for p in Participation.objects.select_related("joueur")}
    assert noms == {"Abel", "Leroy"}


def test_une_duree_hors_plage_reste_sur_le_formulaire(
    page_formatee: Page, live_server, groupe: None
) -> None:
    page = page_formatee
    _se_connecter(page, live_server.url)
    page.goto(live_server.url + "/seances/nouvelle/")

    # Le navigateur bloquerait l'envoi (min et max sur le champ) : on le contourne pour
    # vérifier le refus côté serveur.
    page.locator("main form").evaluate("formulaire => formulaire.noValidate = true")
    page.get_by_label("Durée (minutes)").fill("0")
    page.get_by_role("button", name="Créer la séance").click()

    expect(page).to_have_url(live_server.url + "/seances/nouvelle/")
    expect(page.get_by_text("supérieure ou égale à 1")).to_be_visible()
    assert Seance.objects.count() == 0
