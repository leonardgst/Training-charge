"""Parcours E1 : séance de 25 joueurs saisie au clavier, sur ordinateur et sur tablette.

Le préparateur crée la séance, saisit la grille ligne après ligne avec la seule touche Tab,
enregistre un brouillon à mi-parcours, termine et valide : les charges apparaissent.
"""

import datetime

import pytest
from playwright.sync_api import ConsoleMessage, Page, ViewportSize, expect

from suivi.models import Categorie, Joueur, Participation, Preparateur, Seance

pytestmark = pytest.mark.django_db(transaction=True)

FORMATS: dict[str, ViewportSize] = {
    "ordinateur": {"width": 1280, "height": 800},
    "tablette": {"width": 820, "height": 1180},
}
JOUEURS = 25


def _valeurs(ligne: int) -> tuple[int, int, int]:
    """RPE de la ligne `ligne` (0 pour la première), tous dans l'échelle de 0 à 10."""
    return ligne % 11, (ligne + 3) % 11, (ligne + 6) % 11


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
    Preparateur.objects.create(user=compte, categorie=u19)
    for numero in range(1, JOUEURS + 1):
        Joueur.objects.create(
            nom=f"Joueur{numero:02d}",
            prenom="Test",
            date_naissance=datetime.date(2007, 3, 14),
            categorie_reference=u19,
        )


def _se_connecter(page: Page, url: str) -> None:
    page.goto(url + "/connexion/")
    page.get_by_label("Nom d’utilisateur").fill("preparateur")
    page.get_by_label("Mot de passe").fill("mot-de-passe-de-test-1")
    page.get_by_role("button", name="Se connecter").click()


def _saisir_au_clavier(page: Page, lignes: range) -> None:
    """Tape les trois RPE de chaque ligne, en passant d'une case à l'autre par Tab."""
    for ligne in lignes:
        for valeur in _valeurs(ligne):
            page.keyboard.type(str(valeur))
            page.keyboard.press("Tab")


def test_e1_seance_de_25_joueurs_saisie_au_clavier_puis_validee(
    page_formatee: Page, live_server, groupe: None
) -> None:
    page = page_formatee
    violations: list[str] = []

    def noter(message: ConsoleMessage) -> None:
        if "Content Security Policy" in message.text:
            violations.append(message.text)

    page.on("console", noter)
    _se_connecter(page, live_server.url)
    page.get_by_role("link", name="Nouvelle séance").click()
    page.get_by_label("Durée (minutes)").fill("90")
    page.get_by_role("button", name="Créer la séance").click()
    expect(page.locator("input.rpe")).to_have_count(3 * JOUEURS)

    # Dix premières lignes, au clavier, puis brouillon.
    page.get_by_label("RPE cardio de Test Joueur01").click()
    _saisir_au_clavier(page, range(10))
    page.get_by_role("button", name="Enregistrer le brouillon").click()
    expect(page.get_by_role("status")).to_have_text("Le brouillon est enregistré.")
    expect(page.get_by_label("RPE TETA de Test Joueur10")).to_have_value(str(_valeurs(9)[2]))
    expect(page.get_by_label("RPE cardio de Test Joueur11")).to_have_value("")

    # Code couleur pendant la frappe : la case prend la teinte de sa valeur.
    case = page.get_by_label("RPE cardio de Test Joueur11")
    case.click()
    page.keyboard.type("12")
    expect(case).to_have_attribute("data-niveau", "invalide")
    expect(case).to_have_attribute("aria-invalid", "true")
    page.keyboard.press("Backspace")
    page.keyboard.press("Backspace")
    page.keyboard.type("9")
    expect(case).to_have_attribute("data-niveau", "9")
    expect(case).to_have_css("background-color", "rgb(244, 125, 95)")
    page.keyboard.press("Backspace")

    # Quinze lignes restantes, puis validation.
    _saisir_au_clavier(page, range(10, JOUEURS))
    page.get_by_role("button", name="Valider la séance").click()

    expect(page.get_by_role("status")).to_have_text(
        "La séance est validée : les charges sont calculées."
    )
    expect(page.get_by_text("Foot · 90 min · Validée")).to_be_visible()
    lignes = page.locator("table.grille-rpe tbody tr")
    expect(lignes).to_have_count(JOUEURS)
    # Charges calculées à la main : ligne 1, (0 + 3 + 6) / 3 × 90 × 10 = 2 700 ;
    # ligne 25, (2 + 5 + 8) / 3 × 90 × 10 = 4 500.
    expect(lignes.first.locator("td.charge")).to_have_text("2 700")
    expect(lignes.last.locator("td.charge")).to_have_text("4 500")
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    assert violations == []

    seance = Seance.objects.get()
    assert seance.statut == "validee"
    participations = Participation.objects.filter(seance=seance).order_by("joueur__nom")
    assert [(p.rpe_cardio, p.rpe_musculaire, p.rpe_teta) for p in participations] == [
        _valeurs(ligne) for ligne in range(JOUEURS)
    ]


def test_la_grille_tient_sur_un_telephone(page: Page, live_server, groupe: None) -> None:
    page.set_viewport_size({"width": 390, "height": 844})
    _se_connecter(page, live_server.url)
    page.goto(live_server.url + "/seances/nouvelle/")
    page.get_by_label("Durée (minutes)").fill("60")
    page.get_by_role("button", name="Créer la séance").click()

    expect(page.locator("input.rpe")).to_have_count(3 * JOUEURS)
    assert page.evaluate(
        "document.documentElement.scrollWidth <= window.innerWidth && "
        "[...document.querySelectorAll('.overflow-auto')]"
        ".every(zone => zone.scrollWidth <= zone.clientWidth)"
    )
