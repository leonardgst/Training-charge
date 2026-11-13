"""Parcours E2 : le joueur répond sur son téléphone, le badge passe à « Reçu » côté staff."""

import datetime

import pytest
from playwright.sync_api import Page, ViewportSize, expect

from suivi.horloge import aujourd_hui
from suivi.liens import creer_lien
from suivi.models import Categorie, Indicateur, Joueur, Participation, Preparateur, Seance

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
def groupe(django_user_model) -> dict[str, str]:
    compte = django_user_model.objects.create_user(
        "preparateur",
        password="mot-de-passe-de-test-1",  # noqa: S106
    )
    u19 = Categorie.objects.create(code="U19", libelle="U19")
    Preparateur.objects.create(user=compte, categorie=u19)
    Indicateur.objects.create(
        categorie=u19,
        code="fatigue",
        libelle="Fatigue",
        type="note",
        borne_min=0,
        borne_max=10,
        sens="bas_bon",
    )
    seance = Seance.objects.create(
        categorie_organisatrice=u19, date=aujourd_hui(), type="foot", duree_min=90
    )
    chemins = {"seance": f"/seances/{seance.pk}/"}
    for nom in ("Abel", "Bernard"):
        joueur = Joueur.objects.create(
            nom=nom,
            prenom="Hugo",
            date_naissance=datetime.date(2007, 3, 14),
            categorie_reference=u19,
        )
        Participation.objects.create(seance=seance, joueur=joueur)
        chemins[nom] = f"/q/{creer_lien(joueur, compte)}"
    return chemins


def test_le_badge_passe_a_recu_apres_la_reponse_du_joueur(
    page_formatee: Page, live_server, groupe: dict[str, str]
) -> None:
    page = page_formatee

    page.goto(live_server.url + groupe["Abel"])
    page.get_by_label("Fatigue").fill("4")
    page.get_by_role("button", name="Envoyer").click()
    expect(page.get_by_role("status")).to_contain_text("C’est enregistré")

    page.goto(live_server.url + "/connexion/")
    page.get_by_label("Nom d’utilisateur").fill("preparateur")
    page.get_by_label("Mot de passe").fill("mot-de-passe-de-test-1")
    page.get_by_role("button", name="Se connecter").click()
    page.goto(live_server.url + groupe["seance"])

    ligne_abel = page.get_by_role("row").filter(has_text="Abel")
    ligne_bernard = page.get_by_role("row").filter(has_text="Bernard")
    expect(ligne_abel.locator(".badge")).to_have_text("Reçu")
    expect(ligne_bernard.locator(".badge")).to_have_text("Manquant")
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    assert page.evaluate(
        "[...document.querySelectorAll('.overflow-auto')]"
        ".every(zone => zone.scrollWidth <= zone.clientWidth)"
    )
