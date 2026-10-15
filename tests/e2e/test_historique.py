"""Historique, correction et suppression d'une séance dans un vrai navigateur (US-06)."""

import datetime
import re

import pytest
from django.utils import timezone
from playwright.sync_api import Locator, Page, ViewportSize, expect

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
def seance_validee(django_user_model) -> None:
    compte = django_user_model.objects.create_user(
        "preparateur",
        password="mot-de-passe-de-test-1",  # noqa: S106
    )
    u19 = Categorie.objects.create(code="U19", libelle="U19")
    u17 = Categorie.objects.create(code="U17", libelle="U17")
    Preparateur.objects.create(user=compte, categorie=u19)
    naissance = datetime.date(2007, 3, 14)
    seance = Seance.objects.create(
        categorie_organisatrice=u19, date=datetime.date(2026, 10, 15), type="foot", duree_min=90
    )
    for nom, prenom, rpe in [("Abel", "Yanis", (7, 7, 7)), ("Dupont", "Hugo", (5, 6, 4))]:
        joueur = Joueur.objects.create(
            nom=nom, prenom=prenom, date_naissance=naissance, categorie_reference=u19
        )
        Participation.objects.create(
            seance=seance,
            joueur=joueur,
            rpe_cardio=rpe[0],
            rpe_musculaire=rpe[1],
            rpe_teta=rpe[2],
        )
    Joueur.objects.create(
        nom="Leroy", prenom="Noah", date_naissance=naissance, categorie_reference=u17
    )
    seance.statut = "validee"
    seance.validated_at = timezone.now()
    seance.save()


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


def _charge(page: Page, nom: str) -> Locator:
    ligne = page.locator("table.grille-rpe tbody tr").filter(has_text=nom)
    return ligne.locator("td.charge")


def test_corriger_puis_supprimer_une_seance_validee(
    page_formatee: Page, live_server, seance_validee: None
) -> None:
    page = page_formatee
    _se_connecter(page, live_server.url)
    page.get_by_role("link", name="Séances", exact=True).click()
    assert _sans_debordement(page)
    page.get_by_role("link", name="15/10/2026").click()
    # Calculée à la main : (5 + 6 + 4) / 3 × 90 × 10 = 4 500.
    expect(_charge(page, "Dupont")).to_have_text("4 500")

    # Correction d'un RPE : la séance reste validée, la charge suit.
    page.get_by_role("button", name="Corriger les RPE ou les participants").click()
    page.get_by_label("RPE cardio de Hugo Dupont").fill("9")
    page.get_by_role("button", name="Enregistrer les corrections").click()
    expect(page.get_by_role("status")).to_have_text(
        "Les corrections sont enregistrées : les charges sont recalculées."
    )
    expect(page.get_by_text("Foot · 90 min · Validée")).to_be_visible()
    # (9 + 6 + 4) / 3 × 90 × 10 = 5 700.
    expect(_charge(page, "Dupont")).to_have_text("5 700")

    # Un joueur invité ajouté à la séance validée, avec ses trois RPE.
    page.get_by_role("button", name="Corriger les RPE ou les participants").click()
    page.get_by_role("heading", name="Participants (2)").click()
    page.get_by_role("searchbox", name="Nom ou prénom du joueur").fill("ler")
    page.get_by_role("button", name="Rechercher").click()
    expect(page.get_by_text("Leroy Noah (U17)")).to_be_visible()
    assert _sans_debordement(page)
    page.get_by_label("RPE cardio de Noah Leroy").fill("3")
    page.get_by_label("RPE musculaire de Noah Leroy").fill("3")
    page.get_by_label("RPE teta de Noah Leroy").fill("3")
    page.get_by_role("button", name="Ajouter Noah Leroy").click()
    expect(page.get_by_role("status")).to_have_text("Noah Leroy est ajouté à la séance.")
    expect(page.get_by_label("RPE TETA de Noah Leroy")).to_have_value("3")
    assert _sans_debordement(page)

    # En-tête : la durée passe à 60 minutes, les charges sont recalculées.
    page.get_by_role("link", name="Modifier l’en-tête").click()
    page.get_by_label("Durée (minutes)").fill("60")
    page.get_by_role("button", name="Enregistrer").click()
    expect(page.get_by_role("status")).to_have_text("L’en-tête de la séance est modifié.")
    # (9 + 6 + 4) / 3 × 60 × 10 = 3 800 ; Leroy : 3 × 60 × 10 = 1 800.
    expect(_charge(page, "Dupont")).to_have_text("3 800")
    expect(_charge(page, "Leroy")).to_have_text("1 800")

    # Suppression, après confirmation.
    page.get_by_role("link", name="Supprimer la séance").click()
    expect(page.get_by_role("heading", name=re.compile("Supprimer la séance du"))).to_be_visible()
    expect(page.get_by_text("3 participants")).to_be_visible()
    page.get_by_role("button", name="Supprimer définitivement").click()
    expect(page).to_have_url(live_server.url + "/seances/")
    expect(page.get_by_role("status")).to_have_text("La séance du 15/10/2026 est supprimée.")
    expect(page.get_by_text("Aucune séance dans la catégorie.")).to_be_visible()
    assert Seance.objects.count() == 0
    assert Participation.objects.count() == 0
