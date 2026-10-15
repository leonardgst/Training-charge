"""Connexion et déconnexion du staff, structure des pages (US-02)."""

import re
import secrets

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.test import Client

from suivi.models import Categorie, Preparateur

pytestmark = pytest.mark.django_db

# Généré à chaque exécution : aucune chaîne qui ressemble à un secret dans le dépôt.
MOT_DE_PASSE = secrets.token_urlsafe(16)
ALERTE = re.compile(r'<p class="erreur" role="alert">(.*?)</p>', re.DOTALL)


@pytest.fixture
def compte() -> User:
    """Compte d'un préparateur U19."""
    utilisateur = User.objects.create_user("prep", password=MOT_DE_PASSE)
    Preparateur.objects.create(
        user=utilisateur, categorie=Categorie.objects.create(code="U19", libelle="U19")
    )
    return utilisateur


def _connecter(client: Client, nom: str, mot_de_passe: str, **extra: str):  # noqa: ANN202
    return client.post("/connexion/", {"username": nom, "password": mot_de_passe, **extra})


def _connecte(client: Client) -> bool:
    return "_auth_user_id" in client.session


# --- Connexion -----------------------------------------------------------------------


def test_des_identifiants_valides_ouvrent_l_accueil(client: Client, compte: object) -> None:
    reponse = _connecter(client, "prep", MOT_DE_PASSE)

    assert reponse.status_code == 302
    assert reponse["Location"] == "/"
    assert _connecte(client)


def test_le_message_d_erreur_ne_dit_pas_quel_identifiant_est_faux(
    client: Client, compte: User
) -> None:
    inactif = get_user_model().objects.create_user(
        "inactif", password=MOT_DE_PASSE, is_active=False
    )
    Preparateur.objects.create(user=inactif, categorie=Categorie.objects.get(code="U19"))
    essais = {
        "compte inconnu": ("inconnu", MOT_DE_PASSE),
        "mauvais mot de passe": ("prep", MOT_DE_PASSE + "x"),
        "compte désactivé": ("inactif", MOT_DE_PASSE),
    }

    messages = {}
    for cas, (nom, mot_de_passe) in essais.items():
        reponse = _connecter(client, nom, mot_de_passe)
        assert reponse.status_code == 200, cas
        assert not _connecte(client), cas
        assert mot_de_passe not in reponse.content.decode(), cas
        messages[cas] = ALERTE.findall(reponse.content.decode())

    assert messages["compte inconnu"] != []
    assert messages["mauvais mot de passe"] == messages["compte inconnu"]
    assert messages["compte désactivé"] == messages["compte inconnu"]


def test_la_page_demandee_est_rouverte_apres_la_connexion(client: Client, compte: object) -> None:
    page = client.get("/", follow=True).content.decode()
    assert '<input type="hidden" name="next" value="/">' in page

    reponse = _connecter(client, "prep", MOT_DE_PASSE, next="/?onglet=1")

    assert reponse["Location"] == "/?onglet=1"


@pytest.mark.parametrize("ailleurs", ["https://exemple.invalid/", "//exemple.invalid/"])
def test_une_redirection_vers_un_autre_site_est_ignoree(
    client: Client, compte: object, ailleurs: str
) -> None:
    reponse = _connecter(client, "prep", MOT_DE_PASSE, next=ailleurs)

    assert reponse.status_code == 302
    assert reponse["Location"] == "/"


def test_un_compte_connecte_qui_revient_sur_la_connexion_va_a_l_accueil(
    client: Client, compte: User
) -> None:
    client.force_login(compte)

    reponse = client.get("/connexion/")

    assert reponse.status_code == 302
    assert reponse["Location"] == "/"


# --- Déconnexion ---------------------------------------------------------------------


def test_la_deconnexion_ferme_la_session(client: Client, compte: User) -> None:
    client.force_login(compte)

    reponse = client.post("/deconnexion/")

    assert reponse.status_code == 302
    assert reponse["Location"] == "/connexion/"
    assert not _connecte(client)
    assert client.get("/")["Location"] == "/connexion/?next=/"


def test_la_deconnexion_refuse_une_simple_lecture(client: Client, compte: User) -> None:
    client.force_login(compte)

    assert client.get("/deconnexion/").status_code == 405
    assert _connecte(client)


def test_la_deconnexion_exige_le_jeton_csrf(compte: User) -> None:
    client = Client(enforce_csrf_checks=True)
    client.force_login(compte)

    assert client.post("/deconnexion/").status_code == 403
    assert _connecte(client)


# --- Structure des pages -------------------------------------------------------------


def test_la_navigation_montre_le_compte_la_categorie_et_la_deconnexion(
    client: Client, compte: User
) -> None:
    client.force_login(compte)

    page = client.get("/").content.decode()

    assert '<nav aria-label="Navigation principale">' in page
    assert "prep · U19" in page
    assert '<form method="post" action="/deconnexion/">' in page
    assert 'name="csrfmiddlewaretoken"' in page
    assert "Se déconnecter" in page


def test_la_page_de_connexion_n_a_pas_de_bouton_de_deconnexion(client: Client) -> None:
    page = client.get("/connexion/").content.decode()

    assert "Se déconnecter" not in page
    assert "/static/suivi/vendor/pico/pico.min.css" in page


def test_un_compte_sans_profil_lit_un_refus_en_francais_sans_navigation_du_staff(
    client: Client,
) -> None:
    client.force_login(get_user_model().objects.create_user("sans_profil"))

    reponse = client.get("/")
    page = reponse.content.decode()

    assert reponse.status_code == 403
    assert "Accès refusé" in page
    assert "Se déconnecter" not in page


def test_une_page_introuvable_est_en_francais(client: Client, compte: User) -> None:
    client.force_login(compte)

    reponse = client.get("/n-existe-pas/")

    assert reponse.status_code == 404
    assert "Page introuvable" in reponse.content.decode()
