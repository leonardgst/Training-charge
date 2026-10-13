"""Séances et participations (cas D1, D2 et déclencheur de complétude).

Les contraintes sont vérifiées par SQL direct sous le rôle d'exécution, sans passer
par Django.
"""

import datetime
import time

import psycopg
import pytest
from django.db import IntegrityError, transaction
from django.db.utils import DatabaseError

from suivi.models import Categorie, Joueur, Participation, Seance

pytestmark = pytest.mark.django_db(transaction=True)

JOUR = datetime.date(2026, 10, 12)

INSERT_SEANCE = (
    "INSERT INTO suivi_seance (categorie_organisatrice_id, date, type, duree_min, statut,"
    " validated_at, created_at, updated_at)"
    " VALUES (%s, %s, %s, %s, %s, %s, now(), now()) RETURNING id"
)
INSERT_PARTICIPATION = (
    "INSERT INTO suivi_participation (seance_id, joueur_id, rpe_cardio, rpe_musculaire,"
    " rpe_teta, updated_at) VALUES (%s, %s, %s, %s, %s, now())"
)


@pytest.fixture
def u19() -> Categorie:
    return Categorie.objects.create(code="U19", libelle="Moins de 19 ans")


@pytest.fixture
def joueur(u19: Categorie) -> Joueur:
    return Joueur.objects.create(
        nom="Martin",
        prenom="Lucas",
        date_naissance=datetime.date(2007, 3, 14),
        categorie_reference=u19,
    )


def _seance(categorie: Categorie, **champs: object) -> Seance:
    valeurs: dict[str, object] = {
        "categorie_organisatrice": categorie,
        "date": JOUR,
        "type": "foot",
        "duree_min": 90,
    }
    return Seance.objects.create(**{**valeurs, **champs})


def _valider(seance: Seance) -> None:
    seance.statut = "validee"
    seance.validated_at = datetime.datetime(2026, 10, 12, 20, tzinfo=datetime.UTC)
    seance.save()


def test_seance_creee_en_brouillon_par_defaut(u19: Categorie) -> None:
    seance = _seance(u19)
    seance.refresh_from_db()
    assert seance.statut == "brouillon"
    assert seance.validated_at is None


@pytest.mark.parametrize("duree", [0, -5, 301, 900])
def test_d1_duree_hors_plage_rejetee_par_la_base(
    u19: Categorie, connexion_execution: psycopg.Connection, duree: int
) -> None:
    with pytest.raises(psycopg.errors.CheckViolation):
        connexion_execution.execute(INSERT_SEANCE, (u19.pk, JOUR, "foot", duree, "brouillon", None))


@pytest.mark.parametrize("duree", [1, 300])
def test_d1_bornes_de_duree_acceptees(
    u19: Categorie, connexion_execution: psycopg.Connection, duree: int
) -> None:
    connexion_execution.execute(INSERT_SEANCE, (u19.pk, JOUR, "foot", duree, "brouillon", None))


@pytest.mark.parametrize(
    ("type_seance", "statut"),
    [("danse", "brouillon"), ("foot", "archivee")],
)
def test_d1_type_ou_statut_hors_liste_rejete_par_la_base(
    u19: Categorie, connexion_execution: psycopg.Connection, type_seance: str, statut: str
) -> None:
    with pytest.raises(psycopg.errors.CheckViolation):
        connexion_execution.execute(INSERT_SEANCE, (u19.pk, JOUR, type_seance, 90, statut, None))


def test_validated_at_coherent_avec_le_statut(
    u19: Categorie, connexion_execution: psycopg.Connection
) -> None:
    maintenant = datetime.datetime(2026, 10, 12, 20, tzinfo=datetime.UTC)
    with pytest.raises(psycopg.errors.CheckViolation):
        connexion_execution.execute(INSERT_SEANCE, (u19.pk, JOUR, "foot", 90, "validee", None))
    with pytest.raises(psycopg.errors.CheckViolation):
        connexion_execution.execute(
            INSERT_SEANCE, (u19.pk, JOUR, "foot", 90, "brouillon", maintenant)
        )


@pytest.mark.parametrize("colonne", [0, 1, 2])
@pytest.mark.parametrize("valeur", [-1, 11, 100])
def test_d1_rpe_hors_plage_rejete_par_la_base(
    u19: Categorie,
    joueur: Joueur,
    connexion_execution: psycopg.Connection,
    colonne: int,
    valeur: int,
) -> None:
    seance = _seance(u19)
    rpe: list[int | None] = [5, 5, 5]
    rpe[colonne] = valeur
    with pytest.raises(psycopg.errors.CheckViolation):
        connexion_execution.execute(INSERT_PARTICIPATION, (seance.pk, joueur.pk, *rpe))


@pytest.mark.parametrize("valeur", [0, 10])
def test_d1_bornes_de_rpe_acceptees(
    u19: Categorie, joueur: Joueur, connexion_execution: psycopg.Connection, valeur: int
) -> None:
    seance = _seance(u19)
    connexion_execution.execute(
        INSERT_PARTICIPATION, (seance.pk, joueur.pk, valeur, valeur, valeur)
    )


def test_brouillon_accepte_des_rpe_absents(u19: Categorie, joueur: Joueur) -> None:
    seance = _seance(u19)
    participation = Participation.objects.create(seance=seance, joueur=joueur, rpe_cardio=6)
    participation.refresh_from_db()
    assert participation.rpe_musculaire is None


def test_d2_participation_en_double_rejetee(u19: Categorie, joueur: Joueur) -> None:
    seance = _seance(u19)
    Participation.objects.create(seance=seance, joueur=joueur)
    with pytest.raises(IntegrityError), transaction.atomic():
        Participation.objects.create(seance=seance, joueur=joueur)


def test_declencheur_refuse_la_validation_avec_une_participation_incomplete(
    u19: Categorie, joueur: Joueur
) -> None:
    seance = _seance(u19)
    Participation.objects.create(seance=seance, joueur=joueur, rpe_cardio=6, rpe_musculaire=5)
    with pytest.raises(DatabaseError, match="participations incomplètes"), transaction.atomic():
        _valider(seance)
    seance.refresh_from_db()
    assert seance.statut == "brouillon"


def test_declencheur_accepte_la_validation_quand_tout_est_saisi(
    u19: Categorie, joueur: Joueur
) -> None:
    seance = _seance(u19)
    Participation.objects.create(
        seance=seance, joueur=joueur, rpe_cardio=6, rpe_musculaire=5, rpe_teta=4
    )
    _valider(seance)
    seance.refresh_from_db()
    assert seance.statut == "validee"


def test_declencheur_refuse_une_participation_incomplete_dans_une_seance_validee(
    u19: Categorie, joueur: Joueur
) -> None:
    seance = _seance(u19)
    _valider(seance)
    with pytest.raises(DatabaseError, match="participation incomplète"), transaction.atomic():
        Participation.objects.create(seance=seance, joueur=joueur, rpe_cardio=6)
    Participation.objects.create(
        seance=seance, joueur=joueur, rpe_cardio=6, rpe_musculaire=5, rpe_teta=4
    )


def test_declencheur_refuse_d_effacer_un_rpe_dans_une_seance_validee(
    u19: Categorie, joueur: Joueur
) -> None:
    seance = _seance(u19)
    participation = Participation.objects.create(
        seance=seance, joueur=joueur, rpe_cardio=6, rpe_musculaire=5, rpe_teta=4
    )
    _valider(seance)
    participation.rpe_teta = None
    with pytest.raises(DatabaseError), transaction.atomic():
        participation.save()


def test_declencheur_applique_sous_le_role_d_execution(
    u19: Categorie, joueur: Joueur, connexion_execution: psycopg.Connection
) -> None:
    ligne = connexion_execution.execute(
        INSERT_SEANCE,
        (u19.pk, JOUR, "foot", 90, "validee", datetime.datetime(2026, 10, 12, tzinfo=datetime.UTC)),
    ).fetchone()
    assert ligne is not None
    with pytest.raises(psycopg.errors.CheckViolation):
        connexion_execution.execute(INSERT_PARTICIPATION, (ligne[0], joueur.pk, 5, None, 5))


def test_supprimer_une_seance_supprime_ses_participations(u19: Categorie, joueur: Joueur) -> None:
    seance = _seance(u19)
    Participation.objects.create(seance=seance, joueur=joueur)
    seance.delete()
    assert not Participation.objects.exists()


def test_updated_at_change_sur_une_seance_et_une_participation(
    u19: Categorie, joueur: Joueur
) -> None:
    seance = _seance(u19)
    participation = Participation.objects.create(seance=seance, joueur=joueur)
    avant_seance, avant_participation = seance.updated_at, participation.updated_at
    time.sleep(0.01)
    seance.duree_min = 60
    seance.save()
    participation.rpe_cardio = 7
    participation.save()
    seance.refresh_from_db()
    participation.refresh_from_db()
    assert seance.updated_at > avant_seance
    assert participation.updated_at > avant_participation


def test_categorie_organisatrice_protegee_contre_la_suppression(u19: Categorie) -> None:
    _seance(u19)
    with pytest.raises(IntegrityError), transaction.atomic():
        u19.delete()
