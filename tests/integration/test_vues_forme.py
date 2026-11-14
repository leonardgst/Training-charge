"""Page « Forme actuelle » (US-10, F11, ADR-0018) : périmètre d'accès (A3) et états affichés."""

import datetime
import json
import re
import secrets
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client
from django.utils import timezone

from suivi.models import Categorie, Joueur, Participation, Preparateur, Seance, StatutSeance

pytestmark = pytest.mark.django_db

FIN = datetime.date(2026, 10, 30)


@pytest.fixture
def demo(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("suivi.views.forme.aujourd_hui", lambda: FIN)
    call_command("generer_demo", fin=FIN, mot_de_passe=secrets.token_urlsafe(12), verbosity=0)


def _page(compte: str) -> str:
    client = Client()
    client.force_login(get_user_model().objects.get(username=compte))
    reponse = client.get("/forme/")
    assert reponse.status_code == 200
    return reponse.content.decode()


def _noms(categorie: str, *, actif: bool) -> set[str]:
    return {
        f"{j.prenom} {j.nom}"
        for j in Joueur.objects.filter(categorie_reference__code=categorie, actif=actif)
    }


def test_un_visiteur_anonyme_est_renvoye_vers_la_connexion() -> None:
    reponse = Client().get("/forme/")
    assert reponse.status_code == 302
    assert "/connexion/" in reponse["Location"]


def test_a3_la_page_ne_liste_que_les_joueurs_de_la_categorie_de_reference(demo: None) -> None:
    page = _page("prep_u19")
    for nom in _noms("U19", actif=True):
        assert nom in page
    for nom in _noms("U17", actif=True):
        assert nom not in page
    page17 = _page("prep_u17")
    for nom in _noms("U19", actif=True):
        assert nom not in page17


def test_la_page_donne_un_tableau_de_valeurs_et_la_liste_des_joueurs_sans_point(
    demo: None,
) -> None:
    page = _page("prep_u19")
    assert 'id="valeurs-forme"' in page
    assert 'id="specification-forme"' in page
    actifs = _noms("U19", actif=True)
    tableau = page.split('id="valeurs-forme"')[1].split("</table>")[0]
    avec = set(re.findall(r'<th scope="row">([^<]+)</th>', tableau))
    reste = page.split("Joueurs sans point")[1]
    sans = set(re.findall(r'<th scope="row">([^<]+)</th>', reste))
    assert avec and avec.isdisjoint(sans)
    assert avec | sans == actifs
    assert avec.isdisjoint(_noms("U19", actif=False))


def test_la_page_ne_depend_d_aucun_script_ni_style_en_ligne(demo: None) -> None:
    page = _page("prep_u19")
    assert "<style" not in page
    assert not re.search(r"\sstyle\s*=", page)
    assert not re.search(r"\son[a-z]+\s*=", page)
    balises = re.findall(r"<script\b[^>]*>", page)
    assert balises
    for balise in balises:
        # Un script externe, ou le bloc de données JSON de la spécification, jamais exécuté.
        assert "src=" in balise or 'type="application/json"' in balise


def _joueurs_du_graphique(page: str) -> set[str]:
    bloc = re.search(r'<script id="specification-forme"[^>]*>(.*?)</script>', page, re.S)
    assert bloc
    couche_points = json.loads(bloc.group(1))["layer"][-1]
    return {p["joueur"] for p in couche_points["data"]["values"]}


def test_a3_le_graphique_ne_contient_que_les_joueurs_de_la_categorie_de_reference(
    demo: None,
) -> None:
    joueurs19 = _joueurs_du_graphique(_page("prep_u19"))
    joueurs17 = _joueurs_du_graphique(_page("prep_u17"))
    assert joueurs19 and joueurs17
    assert joueurs19 <= _noms("U19", actif=True)
    assert joueurs17 <= _noms("U17", actif=True)


def test_un_preparateur_ne_peut_pas_envoyer_de_donnees_a_la_page(demo: None) -> None:
    client = Client()
    client.force_login(get_user_model().objects.get(username="prep_u19"))
    assert client.post("/forme/").status_code == 405


def test_les_joueurs_sans_point_sont_listes_avec_leur_etat() -> None:
    u19 = Categorie.objects.create(code="U19", libelle="U19")
    compte = get_user_model().objects.create_user("p19")
    Preparateur.objects.create(user=compte, categorie=u19)
    naissance = datetime.date(2007, 3, 14)
    neuf, absent, archive = (
        Joueur.objects.create(
            nom=nom, prenom="Test", date_naissance=naissance, categorie_reference=u19, actif=actif
        )
        for nom, actif in (("Neuf", True), ("Absent", True), ("Archive", False))
    )
    seance = Seance.objects.create(
        categorie_organisatrice=u19,
        date=FIN - datetime.timedelta(days=12),
        type="foot",
        duree_min=90,
    )
    Participation.objects.create(
        seance=seance, joueur=absent, rpe_cardio=5, rpe_musculaire=5, rpe_teta=5
    )
    Seance.objects.filter(pk=seance.pk).update(
        statut=StatutSeance.VALIDEE, validated_at=timezone.now()
    )
    with patch("suivi.views.forme.aujourd_hui", return_value=FIN):
        client = Client()
        client.force_login(compte)
        page = client.get("/forme/").content.decode()
    sans = page.split("Joueurs sans point")[1]
    assert re.search(r"Test Absent</th><td>Absent depuis 12 jours</td>", sans)
    assert re.search(r"Test Neuf</th><td>Historique insuffisant</td>", sans)
    assert archive.nom not in page
    assert neuf.pk and absent.pk
