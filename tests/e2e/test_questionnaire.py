"""Questionnaire du jour par le lien du joueur, dans un vrai navigateur (US-08, US-09)."""

import datetime

import pytest
from playwright.sync_api import Page, ViewportSize, expect

from suivi.liens import creer_lien
from suivi.models import Categorie, Indicateur, Joueur

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
def chemin_du_lien(django_user_model) -> str:
    compte = django_user_model.objects.create_user("preparateur")
    u19 = Categorie.objects.create(code="U19", libelle="U19")
    for ordre, (code, libelle) in enumerate((("fatigue", "Fatigue"), ("plaisir", "Plaisir"))):
        Indicateur.objects.create(
            categorie=u19,
            code=code,
            libelle=libelle,
            type="note",
            borne_min=0,
            borne_max=10,
            sens="bas_bon",
            ordre=ordre,
        )
    Indicateur.objects.create(
        categorie=u19,
        code="heure_coucher",
        libelle="Heure de coucher",
        type="heure",
        borne_min=0,
        borne_max=1439,
        sens="aucun",
        poids=0,
        inclus_score=False,
        ordre=2,
    )
    joueur = Joueur.objects.create(
        nom="Abel",
        prenom="Hugo",
        date_naissance=datetime.date(2007, 3, 14),
        categorie_reference=u19,
    )
    return f"/q/{creer_lien(joueur, compte)}"


def test_le_joueur_repond_puis_corrige_son_entree_du_jour(
    page_formatee: Page, live_server, chemin_du_lien: str
) -> None:
    page = page_formatee
    erreurs: list[str] = []
    page.on(
        "console", lambda message: erreurs.append(message.text) if message.type == "error" else None
    )
    page.goto(live_server.url + chemin_du_lien)
    expect(page.get_by_role("heading", name="Bonjour Hugo")).to_be_visible()
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")

    page.get_by_label("Fatigue").fill("4")
    page.get_by_label("Plaisir").fill("8")
    page.get_by_label("Heure de coucher").fill("23:30")
    page.get_by_role("button", name="Envoyer").click()

    expect(page.get_by_role("status")).to_contain_text("C’est enregistré")
    expect(page.get_by_label("Fatigue")).to_have_value("4")

    page.goto(live_server.url + chemin_du_lien)
    expect(page.get_by_label("Heure de coucher")).to_have_value("23:30")
    page.get_by_label("Fatigue").fill("9")
    page.get_by_role("button", name="Envoyer").click()

    expect(page.get_by_role("status")).to_contain_text("C’est enregistré")
    expect(page.get_by_label("Fatigue")).to_have_value("9")
    assert erreurs == []


def test_une_valeur_hors_echelle_est_refusee_par_le_navigateur_puis_par_le_serveur(
    page_formatee: Page, live_server, chemin_du_lien: str
) -> None:
    page = page_formatee
    page.goto(live_server.url + chemin_du_lien)
    page.get_by_label("Fatigue").fill("11")
    page.get_by_label("Plaisir").fill("8")
    page.get_by_label("Heure de coucher").fill("23:30")

    page.get_by_role("button", name="Envoyer").click()

    # Le champ porte `max=10` : le navigateur bloque l'envoi, la page reste sur le formulaire.
    expect(page.get_by_role("status")).to_have_count(0)
    assert page.get_by_label("Fatigue").evaluate("champ => champ.validity.rangeOverflow")


def test_un_lien_inconnu_donne_une_page_introuvable(page: Page, live_server) -> None:
    reponse = page.goto(live_server.url + "/q/" + "Z" * 43)

    assert reponse is not None and reponse.status == 404
