"""Un visiteur sans session ne voit que la connexion et le contrôle de santé (A1, squelette)."""

import pytest
from django.test import Client


@pytest.fixture
def client() -> Client:
    return Client()


def test_la_racine_redirige_un_visiteur_vers_la_connexion(client: Client) -> None:
    reponse = client.get("/")

    assert reponse.status_code == 302
    assert reponse["Location"] == "/connexion/?next=/"
    assert reponse.content == b""


def test_une_ecriture_anonyme_est_aussi_redirigee_vers_la_connexion(client: Client) -> None:
    reponse = client.post("/")

    assert reponse.status_code == 302
    assert reponse["Location"] == "/connexion/?next=/"


def test_l_administration_exige_une_connexion(client: Client) -> None:
    reponse = client.get("/admin/")

    assert reponse.status_code == 302
    assert reponse["Location"].startswith("/admin/login/")


def test_la_page_de_connexion_est_en_francais_et_demande_les_identifiants(client: Client) -> None:
    reponse = client.get("/connexion/")
    page = reponse.content.decode()

    assert reponse.status_code == 200
    assert '<html lang="fr">' in page
    assert 'name="username"' in page
    assert 'name="password"' in page
    assert "Se connecter" in page


def test_la_page_de_connexion_ne_contient_rien_du_generateur(client: Client) -> None:
    page = client.get("/connexion/").content.decode().lower()

    assert "the install worked" not in page
    assert "l'installation s'est bien déroulée" not in page
    assert "congratulations" not in page


def test_le_controle_de_sante_repond_sans_session(client: Client) -> None:
    reponse = client.get("/sante/")

    assert reponse.status_code == 200
    assert reponse.content == b"ok"


def test_le_controle_de_sante_refuse_l_ecriture(client: Client) -> None:
    assert client.post("/sante/").status_code == 405


def test_une_adresse_inexistante_donne_une_page_d_erreur_sobre(client: Client) -> None:
    reponse = client.get("/n-existe-pas/")
    page = reponse.content.decode()

    assert reponse.status_code == 404
    for trace in ("Traceback", "URLconf", "Request Method", "DEBUG"):
        assert trace not in page
