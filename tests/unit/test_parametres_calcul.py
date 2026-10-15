"""`config/calcul.toml` : lecture et validation des paramètres de calcul."""

from pathlib import Path

import pytest
from django.core.exceptions import ImproperlyConfigured

from engine.modeles import Parametres
from suivi.calculs import CHEMIN_PARAMETRES, lire_parametres, parametres


def _fichier(tmp_path: Path, contenu: str) -> Path:
    chemin = tmp_path / "calcul.toml"
    chemin.write_text(contenu, encoding="utf-8")
    return chemin


def test_le_fichier_du_depot_donne_les_valeurs_des_adr() -> None:
    assert lire_parametres(CHEMIN_PARAMETRES) == Parametres(facteur_echelle_charge=10.0)
    assert parametres() == lire_parametres()


def test_un_facteur_entier_ou_decimal_est_accepte(tmp_path: Path) -> None:
    assert lire_parametres(_fichier(tmp_path, "facteur_echelle_charge = 0.5\n")) == Parametres(0.5)


@pytest.mark.parametrize(
    "contenu",
    [
        "",
        "facteur_echelle_charge = 10\nfenetre_inconnue = 7\n",
        "facteur_echelle_charge = 0\n",
        "facteur_echelle_charge = -3\n",
        'facteur_echelle_charge = "dix"\n',
        "facteur_echelle_charge = true\n",
    ],
)
def test_un_fichier_invalide_est_refuse(tmp_path: Path, contenu: str) -> None:
    with pytest.raises(ImproperlyConfigured):
        lire_parametres(_fichier(tmp_path, contenu))
