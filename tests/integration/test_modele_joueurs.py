"""Catégories, préparateurs et joueurs (cas D1 et D4, `updated_at`, administration).

Les contraintes sont vérifiées par insertion SQL directe, sans passer par Django.
"""

import datetime
import time

import psycopg
import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import Client

from suivi.models import Categorie, Joueur, Preparateur

pytestmark = pytest.mark.django_db(transaction=True)

NAISSANCE = datetime.date(2007, 3, 14)


@pytest.fixture
def u19() -> Categorie:
    return Categorie.objects.create(code="U19", libelle="Moins de 19 ans")


def _joueur(categorie: Categorie, **champs: object) -> Joueur:
    valeurs: dict[str, object] = {
        "nom": "Martin",
        "prenom": "Lucas",
        "date_naissance": NAISSANCE,
        "categorie_reference": categorie,
    }
    return Joueur.objects.create(**{**valeurs, **champs})


def test_categorie_par_defaut_questionnaire_les_sept_jours(u19: Categorie) -> None:
    u19.refresh_from_db()
    assert u19.jours_questionnaire == [0, 1, 2, 3, 4, 5, 6]
    assert u19.active is True


def test_code_de_categorie_unique(u19: Categorie) -> None:
    with pytest.raises(IntegrityError), transaction.atomic():
        Categorie.objects.create(code="U19", libelle="Doublon")


@pytest.mark.parametrize("jours", [[7], [-1], [0, 9]])
def test_jours_de_questionnaire_hors_semaine_rejetes_par_la_base(
    connexion_execution: psycopg.Connection, jours: list[int]
) -> None:
    with pytest.raises(psycopg.errors.CheckViolation):
        connexion_execution.execute(
            "INSERT INTO suivi_categorie (code, libelle, jours_questionnaire, active)"
            " VALUES ('X', 'X', %s::smallint[], true)",
            (jours,),
        )


def test_code_de_categorie_vide_rejete_par_la_base(
    connexion_execution: psycopg.Connection,
) -> None:
    with pytest.raises(psycopg.errors.CheckViolation):
        connexion_execution.execute(
            "INSERT INTO suivi_categorie (code, libelle, jours_questionnaire, active)"
            " VALUES ('  ', 'X', '{0}', true)"
        )


@pytest.mark.parametrize("colonne", ["nom", "prenom"])
@pytest.mark.parametrize("valeur", ["", "   "])
def test_d1_nom_ou_prenom_vide_rejete_par_la_base(
    u19: Categorie, connexion_execution: psycopg.Connection, colonne: str, valeur: str
) -> None:
    champs = {"nom": "Martin", "prenom": "Lucas", colonne: valeur}
    with pytest.raises(psycopg.errors.CheckViolation):
        connexion_execution.execute(
            "INSERT INTO suivi_joueur (nom, prenom, date_naissance, categorie_reference_id,"
            " actif, created_at, updated_at) VALUES (%s, %s, %s, %s, true, now(), now())",
            (champs["nom"], champs["prenom"], NAISSANCE, u19.pk),
        )


@pytest.mark.parametrize("colonne", ["nom", "prenom", "date_naissance", "categorie_reference_id"])
def test_d1_champ_obligatoire_absent_rejete_par_la_base(
    u19: Categorie, connexion_execution: psycopg.Connection, colonne: str
) -> None:
    valeurs: dict[str, object] = {
        "nom": "Martin",
        "prenom": "Lucas",
        "date_naissance": NAISSANCE,
        "categorie_reference_id": u19.pk,
        colonne: None,
    }
    with pytest.raises(psycopg.errors.NotNullViolation):
        connexion_execution.execute(
            "INSERT INTO suivi_joueur (nom, prenom, date_naissance, categorie_reference_id,"
            " actif, created_at, updated_at) VALUES (%s, %s, %s, %s, true, now(), now())",
            tuple(valeurs.values()),
        )


def test_un_seul_profil_preparateur_par_compte(u19: Categorie) -> None:
    compte = get_user_model().objects.create_user("prep")
    Preparateur.objects.create(user=compte, categorie=u19)
    with pytest.raises(IntegrityError), transaction.atomic():
        Preparateur.objects.create(user=compte, categorie=u19)


def test_updated_at_change_a_chaque_modification(u19: Categorie) -> None:
    joueur = _joueur(u19)
    avant = joueur.updated_at
    time.sleep(0.01)
    joueur.prenom = "Hugo"
    joueur.save()
    joueur.refresh_from_db()
    assert joueur.updated_at > avant
    assert joueur.created_at <= avant


def test_d4_archivage_conserve_le_joueur_et_le_retire_des_listes(u19: Categorie) -> None:
    joueur = _joueur(u19)
    joueur.actif = False
    joueur.save()
    assert Joueur.objects.filter(pk=joueur.pk).exists()
    assert not Joueur.objects.filter(actif=True, pk=joueur.pk).exists()
    joueur.actif = True
    joueur.save()
    assert Joueur.objects.filter(actif=True, pk=joueur.pk).exists()


def test_categorie_avec_joueurs_ne_peut_pas_etre_supprimee(u19: Categorie) -> None:
    _joueur(u19)
    with pytest.raises(IntegrityError), transaction.atomic():
        u19.delete()


def test_administration_fermee_a_un_preparateur(u19: Categorie) -> None:
    compte = get_user_model().objects.create_user("prep")
    Preparateur.objects.create(user=compte, categorie=u19)
    client = Client()
    client.force_login(compte)
    reponse = client.get("/admin/")
    assert reponse.status_code == 302
    assert "/admin/login/" in reponse["Location"]


def test_administration_ouverte_au_superutilisateur_et_trace_l_auteur(u19: Categorie) -> None:
    admin = get_user_model().objects.create_superuser("admin")
    client = Client()
    client.force_login(admin)
    assert client.get("/admin/suivi/joueur/").status_code == 200
    reponse = client.post(
        "/admin/suivi/joueur/add/",
        {
            "nom": "Durand",
            "prenom": "Hugo",
            "date_naissance": "2007-05-01",
            "categorie_reference": u19.pk,
            "actif": "on",
        },
    )
    assert reponse.status_code == 302
    assert Joueur.objects.get(nom="Durand").updated_by == admin
