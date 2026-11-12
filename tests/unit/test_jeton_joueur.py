"""Jeton du lien joueur : génération, empreinte et QR code (US-07, ADR-0006)."""

import hashlib
import re
from urllib.parse import unquote

from suivi.liens import empreinte, generer_jeton, qr_data_uri

ALPHABET_URL = re.compile(r"^[A-Za-z0-9_-]+$")


def test_le_jeton_fait_43_caracteres_d_un_alphabet_sur_dans_une_adresse() -> None:
    jeton = generer_jeton()

    assert len(jeton) == 43
    assert ALPHABET_URL.match(jeton)


def test_deux_jetons_successifs_different() -> None:
    assert len({generer_jeton() for _ in range(200)}) == 200


def test_l_empreinte_est_le_sha256_hexadecimal_du_jeton() -> None:
    assert empreinte("abc") == hashlib.sha256(b"abc").hexdigest()
    assert len(empreinte(generer_jeton())) == 64


def test_l_empreinte_ne_contient_pas_le_jeton() -> None:
    jeton = generer_jeton()

    assert jeton not in empreinte(jeton)


def test_le_qr_code_est_une_image_svg_sans_style_ni_ressource_tierce() -> None:
    adresse = "https://exemple.test/q/" + generer_jeton()

    uri = qr_data_uri(adresse)

    assert uri.startswith("data:image/svg+xml")
    contenu = unquote(uri)
    assert "<svg" in contenu
    assert "style=" not in contenu
    assert "http://" not in contenu.replace("http://www.w3.org/2000/svg", "")
    assert "https://" not in contenu
