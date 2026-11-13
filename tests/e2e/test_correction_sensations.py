"""Le préparateur corrige puis supprime une entrée de sensations passée (F17)."""

import datetime

import pytest
from playwright.sync_api import Page, ViewportSize, expect

from suivi.models import Categorie, EntreeSensations, Indicateur, Joueur, Preparateur, Reponse

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
def donnees(django_user_model) -> None:
    compte = django_user_model.objects.create_user(
        "preparateur",
        password="mot-de-passe-de-test-1",  # noqa: S106
    )
    u19 = Categorie.objects.create(code="U19", libelle="U19")
    Preparateur.objects.create(user=compte, categorie=u19)
    fatigue = Indicateur.objects.create(
        categorie=u19,
        code="fatigue",
        libelle="Fatigue",
        type="note",
        borne_min=0,
        borne_max=10,
        sens="bas_bon",
    )
    joueur = Joueur.objects.create(
        nom="Abel",
        prenom="Hugo",
        date_naissance=datetime.date(2007, 3, 14),
        categorie_reference=u19,
    )
    for jour in (datetime.date(2026, 11, 11), datetime.date(2026, 11, 12)):
        entree = EntreeSensations.objects.create(joueur=joueur, date=jour)
        Reponse.objects.create(entree=entree, indicateur=fatigue, valeur=9)


def test_corriger_puis_supprimer_une_entree_passee(
    page_formatee: Page, live_server, donnees: None
) -> None:
    page = page_formatee
    page.goto(live_server.url + "/connexion/")
    page.get_by_label("Nom d’utilisateur").fill("preparateur")
    page.get_by_label("Mot de passe").fill("mot-de-passe-de-test-1")
    page.get_by_role("button", name="Se connecter").click()
    page.get_by_role("link", name="Joueurs").click()

    page.get_by_role("link", name="Sensations de Hugo Abel").click()
    expect(page.get_by_role("heading", name="Sensations de Hugo Abel")).to_be_visible()
    page.get_by_role("link", name="Corriger l’entrée du 12/11/2026").click()
    page.get_by_label("Fatigue").fill("3")
    page.get_by_role("button", name="Enregistrer la correction").click()

    expect(page.get_by_role("status")).to_contain_text("est corrigée")
    expect(page.get_by_text("corrigée par preparateur")).to_have_count(1)
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")

    page.get_by_role("link", name="Supprimer l’entrée du 11/11/2026").click()
    page.get_by_role("button", name="Supprimer définitivement").click()

    expect(page.get_by_role("status")).to_contain_text("est supprimée")
    expect(page.get_by_role("link", name="Corriger l’entrée du 11/11/2026")).to_have_count(0)
    expect(page.get_by_role("link", name="Corriger l’entrée du 12/11/2026")).to_be_visible()
    assert Reponse.objects.get().valeur == 3
