"""Réglages : refus par défaut, langue et fuseau, `.env.example` complet."""

import ast
import importlib.util
import re
from pathlib import Path

import pytest
from django.conf import settings

RACINE = Path(__file__).resolve().parents[2]
FICHIER_REGLAGES = RACINE / "config" / "settings.py"
FICHIER_ENV_EXEMPLE = RACINE / ".env.example"


def variables_lues(fichier: Path) -> set[str]:
    """Noms lus par `os.environ.get("X", ...)` ou `os.environ["X"]` dans un fichier Python."""
    noms: set[str] = set()
    for noeud in ast.walk(ast.parse(fichier.read_text(encoding="utf-8"))):
        if (
            isinstance(noeud, ast.Call)
            and isinstance(noeud.func, ast.Attribute)
            and noeud.func.attr == "get"
            and ast.unparse(noeud.func.value) == "os.environ"
            and noeud.args
            and isinstance(noeud.args[0], ast.Constant)
        ):
            noms.add(str(noeud.args[0].value))
        elif (
            isinstance(noeud, ast.Subscript)
            and ast.unparse(noeud.value) == "os.environ"
            and isinstance(noeud.slice, ast.Constant)
        ):
            noms.add(str(noeud.slice.value))
    return noms


def variables_declarees(fichier: Path) -> set[str]:
    modele = re.compile(r"^([A-Z][A-Z0-9_]*)=", re.MULTILINE)
    return set(modele.findall(fichier.read_text(encoding="utf-8")))


def test_langue_et_fuseau_du_projet() -> None:
    assert settings.LANGUAGE_CODE == "fr"
    assert settings.TIME_ZONE == "Europe/Paris"
    assert settings.USE_TZ is True


def test_le_refus_par_defaut_est_actif() -> None:
    middlewares = settings.MIDDLEWARE
    login_requis = "django.contrib.auth.middleware.LoginRequiredMiddleware"
    authentification = "django.contrib.auth.middleware.AuthenticationMiddleware"

    assert login_requis in middlewares
    assert middlewares.index(login_requis) > middlewares.index(authentification)


def test_sans_variable_d_environnement_les_reglages_sont_fermes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for nom in variables_lues(FICHIER_REGLAGES):
        monkeypatch.delenv(nom, raising=False)
    specification = importlib.util.spec_from_file_location("reglages_nus", FICHIER_REGLAGES)
    assert specification is not None and specification.loader is not None
    reglages = importlib.util.module_from_spec(specification)

    specification.loader.exec_module(reglages)

    assert reglages.SECRET_KEY == ""
    assert reglages.DEBUG is False
    assert reglages.ALLOWED_HOSTS == []


def test_env_exemple_declare_toutes_les_variables_lues_par_les_reglages() -> None:
    lues = variables_lues(FICHIER_REGLAGES)

    assert lues, "aucune variable détectée : le test ne vérifierait rien"
    assert lues <= variables_declarees(FICHIER_ENV_EXEMPLE)
