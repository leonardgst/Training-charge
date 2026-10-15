"""Visiteur non connecté face au catalogue des routes (A1).

Toutes les routes du résolveur d'URL sont parcourues en GET et en POST, sans session :
chacune doit rediriger vers la connexion ou refuser, sauf la liste blanche.
"""

import pytest
from catalogue_acces import LISTE_BLANCHE, catalogue_des_routes, routes_qui_fuient
from django.test import Client

CHEMINS = catalogue_des_routes()


def test_le_catalogue_contient_les_routes_connues() -> None:
    connues = {"/", "/deconnexion/", "/joueurs/", "/joueurs/1/archiver/", "/seances/nouvelle/"}
    assert connues | {"/seances/1/participations/1/retirer/"} <= set(CHEMINS)
    assert {"/seances/", "/seances/1/corriger/", "/seances/1/supprimer/"} <= set(CHEMINS)
    assert LISTE_BLANCHE == {"/connexion/", "/sante/", "/admin/login/"}


@pytest.mark.parametrize("chemin", CHEMINS)
def test_une_route_hors_liste_blanche_ne_donne_rien_a_un_visiteur(chemin: str) -> None:
    assert routes_qui_fuient(Client(), [chemin]) == []
