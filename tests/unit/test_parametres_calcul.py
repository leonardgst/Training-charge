"""`config/calcul.toml` : lecture et validation des paramètres de calcul."""

from pathlib import Path

import pytest
from django.core.exceptions import ImproperlyConfigured

from engine.modeles import Parametres
from suivi.calculs import CHEMIN_PARAMETRES, lire_parametres, parametres

BASE = (
    "facteur_echelle_charge = 10\nfenetre_courte_jours = 7\nfenetre_longue_jours = 28\n"
    "reference_jours = 28\nreference_min_jours = 21\ntolerance_ecart_type_nul = 1e-9\n"
    "score_poids_min = 0.5\nsensations_reference_jours = 28\nsensations_reference_min_entrees = 6\n"
)


def _fichier(tmp_path: Path, contenu: str) -> Path:
    chemin = tmp_path / "calcul.toml"
    chemin.write_text(contenu, encoding="utf-8")
    return chemin


def test_le_fichier_du_depot_donne_les_valeurs_des_adr() -> None:
    assert lire_parametres(CHEMIN_PARAMETRES) == Parametres(10.0, 7, 28, 28, 21, 1e-9, 0.5, 28, 6)
    assert parametres() == lire_parametres()


def test_un_facteur_entier_ou_decimal_est_accepte(tmp_path: Path) -> None:
    assert lire_parametres(
        _fichier(tmp_path, _avec("facteur_echelle_charge", "0.5"))
    ) == Parametres(0.5, 7, 28, 28, 21, 1e-9, 0.5, 28, 6)


def _avec(cle: str, valeur: str) -> str:
    """BASE dont la clé `cle` prend `valeur`."""
    lignes = [
        f"{cle} = {valeur}" if ligne.startswith(f"{cle} =") else ligne
        for ligne in BASE.splitlines()
    ]
    return "\n".join(lignes) + "\n"


@pytest.mark.parametrize(
    "contenu",
    [
        "",
        "facteur_echelle_charge = 10\n",
        BASE + "fenetre_inconnue = 7\n",
        _avec("facteur_echelle_charge", "0"),
        _avec("facteur_echelle_charge", "-3"),
        _avec("facteur_echelle_charge", '"dix"'),
        _avec("facteur_echelle_charge", "true"),
        _avec("fenetre_courte_jours", "0"),
        _avec("fenetre_courte_jours", "7.5"),
        _avec("fenetre_courte_jours", "true"),
        _avec("fenetre_courte_jours", "28"),
        _avec("reference_jours", "0"),
        _avec("reference_min_jours", "1"),
        _avec("reference_min_jours", "29"),
        _avec("tolerance_ecart_type_nul", "0"),
        _avec("tolerance_ecart_type_nul", "false"),
        _avec("score_poids_min", "0"),
        _avec("score_poids_min", "1.5"),
        _avec("sensations_reference_jours", "0"),
        _avec("sensations_reference_min_entrees", "1"),
        _avec("sensations_reference_min_entrees", "29"),
    ],
)
def test_un_fichier_invalide_est_refuse(tmp_path: Path, contenu: str) -> None:
    with pytest.raises(ImproperlyConfigured):
        lire_parametres(_fichier(tmp_path, contenu))
