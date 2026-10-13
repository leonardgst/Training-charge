"""Test de fumée après déploiement : l'URL publique répond comme prévu à un visiteur.

Lancé par le workflow de déploiement avec `SMOKE_URL` ; sans cette variable, il n'a rien
à interroger et reste ignoré.
"""

import email.message
import os
import urllib.error
import urllib.request

import pytest

URL = os.environ.get("SMOKE_URL", "").rstrip("/")

pytestmark = pytest.mark.skipif(not URL, reason="SMOKE_URL non défini : aucun déploiement ciblé")


class _SansRedirection(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args: object, **kwargs: object) -> None:
        return None


def _get(chemin: str) -> tuple[int, email.message.Message]:
    ouvreur = urllib.request.build_opener(_SansRedirection)
    try:
        with ouvreur.open(URL + chemin, timeout=30) as reponse:  # noqa: S310
            return reponse.status, reponse.headers
    except urllib.error.HTTPError as erreur:
        return erreur.code, erreur.headers


def test_le_controle_de_sante_repond() -> None:
    statut, _ = _get("/sante/")

    assert statut == 200


def test_la_racine_redirige_vers_la_connexion() -> None:
    statut, en_tetes = _get("/")

    assert statut == 302
    assert "/connexion/" in en_tetes["Location"]


def test_la_page_de_connexion_s_affiche_en_https_avec_hsts() -> None:
    statut, en_tetes = _get("/connexion/")

    assert URL.startswith("https://")
    assert statut == 200
    assert "max-age=" in en_tetes["Strict-Transport-Security"]


def test_l_administration_demande_une_connexion() -> None:
    statut, en_tetes = _get("/admin/")

    assert statut == 302
    assert "/admin/login/" in en_tetes["Location"]


def test_une_adresse_inexistante_donne_une_erreur_sobre() -> None:
    statut, _ = _get("/cette-page-n-existe-pas/")

    # Le refus par défaut renvoie vers la connexion avant même de chercher la page.
    assert statut in {302, 404}
