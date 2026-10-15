"""Gestion des joueurs dans un vrai navigateur, sur ordinateur, tablette et téléphone (US-15)."""

import datetime

import pytest
from playwright.sync_api import Page, ViewportSize, expect

from suivi.models import Categorie, Joueur, Preparateur

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
    u19 = Categorie.objects.create(code="U19", libelle="U19")
    Preparateur.objects.create(user=compte, categorie=u19)
    for nom in ("Abel", "Bernard", "Dupont", "Petit"):
        Joueur.objects.create(
            nom=nom,
            prenom="Hugo",
            date_naissance=datetime.date(2007, 3, 14),
            categorie_reference=u19,
        )


def _se_connecter(page: Page, url: str) -> None:
    page.goto(url + "/connexion/")
    page.get_by_label("Nom d’utilisateur").fill("preparateur")
    page.get_by_label("Mot de passe").fill("mot-de-passe-de-test-1")
    page.get_by_role("button", name="Se connecter").click()


def _tableaux_sans_debordement(page: Page) -> bool:
    """Chaque tableau tient dans sa zone : aucune colonne n'est cachée hors de l'écran."""
    return page.evaluate(
        "[...document.querySelectorAll('.overflow-auto')]"
        ".every(zone => zone.scrollWidth <= zone.clientWidth)"
    )


def test_ajouter_modifier_archiver_puis_reactiver_un_joueur(
    page_formatee: Page, live_server, preparateur: None
) -> None:
    page = page_formatee
    _se_connecter(page, live_server.url)
    page.get_by_role("link", name="Joueurs").click()
    expect(page.get_by_role("heading", name="Joueurs", exact=True)).to_be_visible()
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")

    page.get_by_role("button", name="Ajouter un joueur").click()
    page.get_by_label("Nom", exact=True).fill("Martin")
    page.get_by_label("Prénom").fill("Lucas")
    page.get_by_label("Date de naissance").fill("2008-05-02")
    page.get_by_role("button", name="Enregistrer").click()
    expect(page.get_by_role("status")).to_have_text("Lucas Martin est ajouté à la catégorie.")
    expect(page.get_by_role("cell", name="Martin Lucas", exact=True)).to_be_visible()
    assert _tableaux_sans_debordement(page)

    page.get_by_role("link", name="Modifier Lucas Martin").click()
    page.get_by_label("Prénom").fill("Luca")
    page.get_by_role("button", name="Enregistrer").click()
    expect(page.get_by_role("status")).to_have_text("Luca Martin est modifié.")

    page.get_by_role("button", name="Archiver Luca Martin").click()
    expect(page.get_by_role("status")).to_contain_text("Luca Martin est archivé")
    expect(page.get_by_role("button", name="Réactiver Luca Martin")).to_be_visible()

    assert _tableaux_sans_debordement(page)

    page.get_by_role("button", name="Réactiver Luca Martin").click()
    expect(page.get_by_role("button", name="Archiver Luca Martin")).to_be_visible()


def test_une_saisie_invalide_reste_sur_le_formulaire_avec_son_message(
    page_formatee: Page, live_server, preparateur: None
) -> None:
    page = page_formatee
    _se_connecter(page, live_server.url)
    page.goto(live_server.url + "/joueurs/nouveau/")

    page.get_by_label("Nom", exact=True).fill("Martin")
    page.get_by_label("Prénom").fill("Lucas")
    page.get_by_label("Date de naissance").fill("2999-01-01")
    page.get_by_role("button", name="Enregistrer").click()

    expect(page).to_have_url(live_server.url + "/joueurs/nouveau/")
    expect(page.get_by_text("La date de naissance ne peut pas être dans le futur.")).to_be_visible()
