"""Jeton du lien joueur : génération, empreinte et QR code (US-07, ADR-0006)."""

import contextlib
import re
from urllib.parse import unquote

import pytest
from django.views.debug import ExceptionReporter

from suivi.liens import creer_lien, empreinte, generer_jeton, qr_data_uri

ALPHABET_URL = re.compile(r"^[A-Za-z0-9_-]+$")


def test_le_jeton_fait_43_caracteres_d_un_alphabet_sur_dans_une_adresse() -> None:
    jeton = generer_jeton()

    assert len(jeton) == 43
    assert ALPHABET_URL.match(jeton)


def test_deux_jetons_successifs_different() -> None:
    assert len({generer_jeton() for _ in range(200)}) == 200


def test_l_empreinte_est_le_sha256_hexadecimal_du_jeton() -> None:
    # Vecteur de test publié de la norme FIPS 180-2 : SHA-256 de « abc ».
    attendu = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    assert empreinte("abc") == attendu
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


def _rapport(erreur: BaseException) -> str:
    return ExceptionReporter(None, type(erreur), erreur, erreur.__traceback__).get_traceback_html()


def test_l_adresse_du_lien_est_masquee_d_un_rapport_d_erreur(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # La panne survient après la création du QR code : aucun cadre de segno ne tient l'adresse.
    faux_qr = type("QR", (), {"svg_data_uri": lambda self, **options: 1 / 0})()
    monkeypatch.setattr("suivi.liens.segno.make_qr", lambda *args, **options: faux_qr)

    with pytest.raises(ZeroDivisionError) as erreur:
        qr_data_uri("https://exemple.test/q/" + "Z" * 43)  # aucune variable locale du test

    rapport = _rapport(erreur.value)  # avant toute variable qui contiendrait le secret

    assert "Z" * 43 not in rapport


def test_le_jeton_est_masque_d_un_rapport_d_erreur(monkeypatch: pytest.MonkeyPatch) -> None:
    class Panne:
        objects = None

        @classmethod
        def select_for_update(cls) -> "Panne":
            raise RuntimeError("panne de base")

    monkeypatch.setattr("suivi.liens.generer_jeton", lambda: "Y" * 43)
    monkeypatch.setattr("suivi.liens.Joueur", type("Joueur", (), {"objects": Panne}))
    monkeypatch.setattr("suivi.liens.transaction.atomic", contextlib.nullcontext)
    joueur = type("J", (), {"pk": 1})()

    with pytest.raises(RuntimeError) as erreur:
        creer_lien(joueur, None)  # type: ignore[arg-type]

    rapport = _rapport(erreur.value)

    assert "Y" * 43 not in rapport
