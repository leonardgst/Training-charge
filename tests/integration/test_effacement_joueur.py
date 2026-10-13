"""Archivage et effacement d'un joueur (D4, ADR-0009)."""

import datetime
import secrets

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import connection
from django.test import Client

from suivi.acces import annuaire, entrees_visibles, joueurs_suivis, participations_visibles
from suivi.models import EntreeSensations, Joueur, Participation, Preparateur, Reponse, Seance

pytestmark = pytest.mark.django_db(transaction=True)

FIN = datetime.date(2026, 10, 12)


@pytest.fixture(autouse=True)
def demonstration() -> None:
    call_command("generer_demo", fin=FIN, mot_de_passe=secrets.token_urlsafe(12), verbosity=0)


def _invite() -> Joueur:
    """Un joueur U17 qui s'est entraîné avec les U19 : il a des données dans deux catégories."""
    participation = (
        Participation.objects.filter(seance__categorie_organisatrice__code="U19")
        .exclude(joueur__categorie_reference__code="U19")
        .select_related("joueur")
        .first()
    )
    assert participation is not None
    return participation.joueur


def _references(joueur_id: int) -> dict[str, int]:
    """Nombre de lignes qui référencent le joueur, dans chaque table, d'après le catalogue."""
    with connection.cursor() as curseur:
        curseur.execute(
            """
            SELECT c.conrelid::regclass::text, a.attname
            FROM pg_constraint c
            JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = ANY (c.conkey)
            WHERE c.contype = 'f' AND c.confrelid = 'suivi_joueur'::regclass
            """
        )
        liens = curseur.fetchall()
        comptes: dict[str, int] = {}
        for table, colonne in liens:
            curseur.execute(f'SELECT count(*) FROM "{table}" WHERE "{colonne}" = %s', [joueur_id])  # noqa: S608
            comptes[f"{table}.{colonne}"] = curseur.fetchone()[0]
    return comptes


def _admin_client() -> Client:
    client = Client()
    client.force_login(get_user_model().objects.get(username="admin_demo"))
    return client


def test_le_catalogue_trouve_les_tables_qui_referencent_un_joueur() -> None:
    comptes = _references(_invite().pk)
    assert {"suivi_participation.joueur_id", "suivi_entreesensations.joueur_id"} <= set(comptes)
    assert all(n > 0 for n in comptes.values())


def test_d4_archivage_retire_des_listes_et_conserve_l_historique() -> None:
    joueur = Joueur.objects.filter(categorie_reference__code="U19", actif=True).first()
    assert joueur is not None
    preparateur = Preparateur.objects.get(categorie=joueur.categorie_reference)
    avant = {
        "participations": Participation.objects.filter(joueur=joueur).count(),
        "entrees": EntreeSensations.objects.filter(joueur=joueur).count(),
    }
    assert joueur.pk in {ligne["pk"] for ligne in annuaire(preparateur)}

    joueur.actif = False
    joueur.save()

    assert joueur.pk not in {ligne["pk"] for ligne in annuaire(preparateur)}
    assert not joueurs_suivis(preparateur).filter(actif=True, pk=joueur.pk).exists()
    # historique consultable par le préparateur de sa catégorie
    assert joueurs_suivis(preparateur).filter(pk=joueur.pk).exists()
    assert (
        participations_visibles(preparateur).filter(joueur=joueur).count()
        == avant["participations"]
    )
    assert entrees_visibles(preparateur).filter(joueur=joueur).count() == avant["entrees"]


def test_d4_effacement_supprime_toute_trace_du_joueur() -> None:
    joueur = _invite()
    identifiant = joueur.pk
    entrees = list(EntreeSensations.objects.filter(joueur=joueur).values_list("pk", flat=True))
    reponses_du_joueur = Reponse.objects.filter(entree_id__in=entrees).count()
    assert reponses_du_joueur > 0
    seances_du_joueur = list(
        Participation.objects.filter(joueur=joueur).values_list("seance_id", flat=True)
    )
    participations_des_autres = Participation.objects.exclude(joueur=joueur).count()
    reponses_des_autres = Reponse.objects.exclude(entree_id__in=entrees).count()
    seances = Seance.objects.count()

    reponse = _admin_client().post(f"/admin/suivi/joueur/{identifiant}/delete/", {"post": "yes"})

    assert reponse.status_code == 302
    assert not Joueur.objects.filter(pk=identifiant).exists()
    # aucune ligne ne référence plus le joueur, dans aucune table
    assert set(_references(identifiant).values()) == {0}
    assert not EntreeSensations.objects.filter(pk__in=entrees).exists()
    assert not Reponse.objects.filter(entree_id__in=entrees).exists()
    # les autres joueurs et les séances partagées sont intacts
    assert Participation.objects.count() == participations_des_autres
    assert Reponse.objects.count() == reponses_des_autres
    assert Seance.objects.count() == seances
    assert Seance.objects.filter(pk__in=seances_du_joueur).count() == len(set(seances_du_joueur))


def test_d4_les_participations_des_autres_joueurs_a_ses_seances_sont_intactes() -> None:
    joueur = _invite()
    seance = Participation.objects.filter(joueur=joueur).first().seance  # type: ignore[union-attr]
    autres = set(
        Participation.objects.filter(seance=seance)
        .exclude(joueur=joueur)
        .values_list("pk", "rpe_cardio")
    )
    assert autres

    _admin_client().post(f"/admin/suivi/joueur/{joueur.pk}/delete/", {"post": "yes"})

    assert (
        set(Participation.objects.filter(seance=seance).values_list("pk", "rpe_cardio")) == autres
    )


def test_d4_un_preparateur_ne_peut_pas_effacer_un_joueur() -> None:
    joueur = Joueur.objects.filter(categorie_reference__code="U19").first()
    assert joueur is not None
    client = Client()
    client.force_login(get_user_model().objects.get(username="prep_u19"))

    reponse = client.post(f"/admin/suivi/joueur/{joueur.pk}/delete/", {"post": "yes"})

    assert reponse.status_code == 302
    assert "/admin/login/" in reponse["Location"]
    assert Joueur.objects.filter(pk=joueur.pk).exists()


def test_d4_la_page_de_confirmation_annonce_la_suppression_en_cascade() -> None:
    joueur = _invite()
    reponse = _admin_client().get(f"/admin/suivi/joueur/{joueur.pk}/delete/")
    page = reponse.content.decode()
    assert reponse.status_code == 200
    assert "Participation" in page
    assert "Entrée" in page or "entrée" in page
