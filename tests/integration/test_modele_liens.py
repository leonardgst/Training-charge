"""Contraintes de la table des liens joueurs, vérifiées en SQL direct (D1, D2, ADR-0006)."""

import datetime

import psycopg
import pytest
from django.db import DataError, IntegrityError, connection, transaction

from suivi.models import Categorie, Joueur, LienJoueur

pytestmark = pytest.mark.django_db

EMPREINTE_A = "a" * 64
EMPREINTE_B = "b" * 64


@pytest.fixture
def joueur() -> Joueur:
    categorie = Categorie.objects.create(code="U19", libelle="U19")
    return Joueur.objects.create(
        nom="Dupont",
        prenom="Hugo",
        date_naissance=datetime.date(2007, 3, 14),
        categorie_reference=categorie,
    )


def _inserer(joueur_id: int, empreinte: str, revoque: bool = False) -> None:
    with connection.cursor() as curseur:
        curseur.execute(
            "INSERT INTO suivi_lienjoueur (joueur_id, token_hash, created_at, revoked_at) "
            "VALUES (%s, %s, now(), CASE WHEN %s THEN now() END)",
            [joueur_id, empreinte, revoque],
        )


def test_un_lien_actif_au_plus_par_joueur(joueur: Joueur) -> None:
    _inserer(joueur.pk, EMPREINTE_A)

    with pytest.raises(IntegrityError), transaction.atomic():
        _inserer(joueur.pk, EMPREINTE_B)


def test_un_lien_revoque_ne_bloque_pas_un_nouveau_lien_actif(joueur: Joueur) -> None:
    _inserer(joueur.pk, EMPREINTE_A, revoque=True)
    _inserer(joueur.pk, EMPREINTE_B)

    assert LienJoueur.objects.filter(joueur=joueur).count() == 2
    assert LienJoueur.objects.filter(joueur=joueur, revoked_at__isnull=True).count() == 1


def test_plusieurs_liens_revoques_peuvent_coexister(joueur: Joueur) -> None:
    _inserer(joueur.pk, EMPREINTE_A, revoque=True)
    _inserer(joueur.pk, EMPREINTE_B, revoque=True)

    assert LienJoueur.objects.filter(joueur=joueur).count() == 2


def test_l_empreinte_est_unique_meme_entre_joueurs(joueur: Joueur) -> None:
    autre = Joueur.objects.create(
        nom="Leroy",
        prenom="Noah",
        date_naissance=datetime.date(2007, 3, 14),
        categorie_reference=joueur.categorie_reference,
    )
    _inserer(joueur.pk, EMPREINTE_A)

    with pytest.raises(IntegrityError), transaction.atomic():
        _inserer(autre.pk, EMPREINTE_A)


@pytest.mark.parametrize(
    "valeur",
    ["", "abc", "a" * 63, "a" * 65, "A" * 64, "g" * 64, "a" * 63 + " "],
    ids=["vide", "courte", "63", "65", "majuscules", "non_hexadecimal", "espace"],
)
def test_l_empreinte_refusee_en_base_si_ce_n_est_pas_un_sha256_hexadecimal(
    joueur: Joueur, valeur: str
) -> None:
    with pytest.raises((IntegrityError, DataError)), transaction.atomic():
        _inserer(joueur.pk, valeur)


def test_le_lien_disparait_avec_le_joueur(joueur: Joueur) -> None:
    _inserer(joueur.pk, EMPREINTE_A)

    joueur.delete()

    assert LienJoueur.objects.count() == 0


def test_le_role_d_execution_lit_ecrit_et_supprime_les_liens(
    connexion_execution: psycopg.Connection, connexion_migration: psycopg.Connection
) -> None:
    connexion_migration.execute(
        "INSERT INTO suivi_categorie (code, libelle, jours_questionnaire, active) "
        "VALUES ('Z1', 'Z1', '{0,1,2,3,4,5,6}', true)"
    )
    connexion_migration.execute(
        "INSERT INTO suivi_joueur (nom, prenom, date_naissance, categorie_reference_id, actif, "
        "created_at, updated_at) SELECT 'N', 'P', '2007-01-01', id, true, now(), now() "
        "FROM suivi_categorie WHERE code = 'Z1'"
    )
    ligne = connexion_migration.execute("SELECT max(id) FROM suivi_joueur").fetchone()
    assert ligne is not None
    joueur_id = ligne[0]

    connexion_execution.execute(
        "INSERT INTO suivi_lienjoueur (joueur_id, token_hash, created_at) VALUES (%s, %s, now())",
        [joueur_id, EMPREINTE_A],
    )
    connexion_execution.execute("UPDATE suivi_lienjoueur SET revoked_at = now()")
    compte = connexion_execution.execute("SELECT count(*) FROM suivi_lienjoueur").fetchone()
    assert compte is not None
    assert compte[0] == 1
    connexion_execution.execute("DELETE FROM suivi_lienjoueur")
    connexion_migration.execute("DELETE FROM suivi_joueur WHERE id = %s", [joueur_id])
    connexion_migration.execute("DELETE FROM suivi_categorie WHERE code = 'Z1'")
