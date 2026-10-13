"""Indicateurs, entrées de sensations et réponses (cas D1, D2, refus de changement d'échelle).

Les contraintes sont vérifiées par SQL direct sous le rôle d'exécution, sans passer
par Django.
"""

import datetime
import time

import psycopg
import pytest
from django.db import IntegrityError, transaction
from django.db.utils import DatabaseError

from suivi.models import Categorie, EntreeSensations, Indicateur, Joueur, Reponse

pytestmark = pytest.mark.django_db(transaction=True)

JOUR = datetime.date(2026, 10, 12)

INSERT_INDICATEUR = (
    "INSERT INTO suivi_indicateur (categorie_id, code, libelle, type, borne_min, borne_max,"
    " sens, poids, inclus_score, ordre, actif)"
    " VALUES (%s, %s, 'X', %s, %s, %s, %s, %s, %s, 0, true)"
)
INSERT_REPONSE = "INSERT INTO suivi_reponse (entree_id, indicateur_id, valeur) VALUES (%s, %s, %s)"


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


@pytest.fixture
def fatigue(u19: Categorie) -> Indicateur:
    return Indicateur.objects.create(
        categorie=u19,
        code="fatigue",
        libelle="Fatigue",
        type="note",
        borne_min=0,
        borne_max=10,
        sens="bas_bon",
    )


@pytest.fixture
def entree(joueur: Joueur) -> EntreeSensations:
    return EntreeSensations.objects.create(joueur=joueur, date=JOUR)


def _indicateur(connexion: psycopg.Connection, categorie: Categorie, **champs: object) -> None:
    valeurs: dict[str, object] = {
        "code": "x",
        "type": "note",
        "borne_min": 0,
        "borne_max": 10,
        "sens": "haut_bon",
        "poids": 1,
        "inclus_score": True,
    }
    v = {**valeurs, **champs}
    connexion.execute(
        INSERT_INDICATEUR,
        (
            categorie.pk,
            v["code"],
            v["type"],
            v["borne_min"],
            v["borne_max"],
            v["sens"],
            v["poids"],
            v["inclus_score"],
        ),
    )


def test_indicateur_valide_accepte(u19: Categorie, connexion_execution: psycopg.Connection) -> None:
    _indicateur(connexion_execution, u19)
    _indicateur(
        connexion_execution,
        u19,
        code="heure_coucher",
        type="heure",
        borne_min=0,
        borne_max=1439,
        sens="aucun",
        poids=0,
        inclus_score=False,
    )


@pytest.mark.parametrize(
    "champs",
    [
        {"borne_min": 5, "borne_max": 5},
        {"borne_min": 8, "borne_max": 2},
        {"poids": -1},
        {"type": "texte"},
        {"sens": "milieu"},
        {"code": "  "},
        {"sens": "aucun", "inclus_score": True},
        {"type": "heure", "borne_min": 0, "borne_max": 24, "sens": "aucun", "inclus_score": False},
        {"type": "heure", "borne_min": 0, "borne_max": 1439, "sens": "aucun"},
    ],
)
def test_d1_indicateur_incoherent_rejete_par_la_base(
    u19: Categorie, connexion_execution: psycopg.Connection, champs: dict[str, object]
) -> None:
    with pytest.raises(psycopg.errors.CheckViolation):
        _indicateur(connexion_execution, u19, **champs)


def test_code_d_indicateur_unique_par_categorie(u19: Categorie, fatigue: Indicateur) -> None:
    autre = Categorie.objects.create(code="U17", libelle="U17")
    Indicateur.objects.create(
        categorie=autre, code="fatigue", libelle="F", type="note", borne_min=0, borne_max=10,
        sens="bas_bon",
    )  # fmt: skip
    with pytest.raises(IntegrityError), transaction.atomic():
        Indicateur.objects.create(
            categorie=u19, code="fatigue", libelle="F", type="note", borne_min=0, borne_max=10,
            sens="bas_bon",
        )  # fmt: skip


@pytest.mark.parametrize("valeur", [-1, 11, 100])
def test_d1_reponse_hors_bornes_rejetee_par_la_base(
    entree: EntreeSensations,
    fatigue: Indicateur,
    connexion_execution: psycopg.Connection,
    valeur: int,
) -> None:
    with pytest.raises(psycopg.errors.CheckViolation):
        connexion_execution.execute(INSERT_REPONSE, (entree.pk, fatigue.pk, valeur))


@pytest.mark.parametrize("valeur", [0, 10])
def test_d1_bornes_de_reponse_acceptees(
    entree: EntreeSensations,
    fatigue: Indicateur,
    connexion_execution: psycopg.Connection,
    valeur: int,
) -> None:
    connexion_execution.execute(INSERT_REPONSE, (entree.pk, fatigue.pk, valeur))


def test_d1_reponse_de_type_heure_dans_les_minutes_du_jour(
    u19: Categorie, entree: EntreeSensations, connexion_execution: psycopg.Connection
) -> None:
    coucher = Indicateur.objects.create(
        categorie=u19,
        code="heure_coucher",
        libelle="Coucher",
        type="heure",
        borne_min=0,
        borne_max=1439,
        sens="aucun",
        poids=0,
        inclus_score=False,
    )
    connexion_execution.execute(INSERT_REPONSE, (entree.pk, coucher.pk, 1380))
    with pytest.raises(psycopg.errors.CheckViolation):
        connexion_execution.execute(INSERT_REPONSE, (entree.pk, coucher.pk, 1440))


def test_d1_modifier_une_reponse_hors_bornes_est_rejete(
    entree: EntreeSensations, fatigue: Indicateur
) -> None:
    reponse = Reponse.objects.create(entree=entree, indicateur=fatigue, valeur=4)
    reponse.valeur = 11
    with pytest.raises(DatabaseError, match="hors des bornes"), transaction.atomic():
        reponse.save()


def test_d2_reponse_en_double_rejetee(entree: EntreeSensations, fatigue: Indicateur) -> None:
    Reponse.objects.create(entree=entree, indicateur=fatigue, valeur=4)
    with pytest.raises(IntegrityError), transaction.atomic():
        Reponse.objects.create(entree=entree, indicateur=fatigue, valeur=5)


def test_d2_seconde_entree_le_meme_jour_rejetee(joueur: Joueur) -> None:
    EntreeSensations.objects.create(joueur=joueur, date=JOUR)
    with pytest.raises(IntegrityError), transaction.atomic():
        EntreeSensations.objects.create(joueur=joueur, date=JOUR)
    EntreeSensations.objects.create(joueur=joueur, date=JOUR + datetime.timedelta(days=1))


def test_d2_seconde_entree_rejetee_sous_le_role_d_execution(
    joueur: Joueur, entree: EntreeSensations, connexion_execution: psycopg.Connection
) -> None:
    with pytest.raises(psycopg.errors.UniqueViolation):
        connexion_execution.execute(
            "INSERT INTO suivi_entreesensations (joueur_id, date, created_at, updated_at)"
            " VALUES (%s, %s, now(), now())",
            (joueur.pk, JOUR),
        )


def test_echelle_modifiable_tant_qu_aucune_reponse_n_existe(fatigue: Indicateur) -> None:
    fatigue.borne_max = 7
    fatigue.save()
    fatigue.refresh_from_db()
    assert fatigue.borne_max == 7


@pytest.mark.parametrize("champ", ["borne_min", "borne_max", "type"])
def test_changement_d_echelle_refuse_des_qu_une_reponse_existe(
    entree: EntreeSensations, fatigue: Indicateur, champ: str
) -> None:
    Reponse.objects.create(entree=entree, indicateur=fatigue, valeur=4)
    setattr(fatigue, champ, {"borne_min": 1, "borne_max": 7, "type": "heure"}[champ])
    with pytest.raises(DatabaseError, match="échelle figée"), transaction.atomic():
        fatigue.save()


def test_libelle_poids_et_desactivation_restent_modifiables_apres_une_reponse(
    entree: EntreeSensations, fatigue: Indicateur
) -> None:
    Reponse.objects.create(entree=entree, indicateur=fatigue, valeur=4)
    fatigue.libelle = "Fatigue générale"
    fatigue.poids = 2
    fatigue.actif = False
    fatigue.save()
    assert Reponse.objects.filter(indicateur=fatigue).count() == 1


def test_un_indicateur_avec_reponses_ne_peut_pas_etre_supprime(
    entree: EntreeSensations, fatigue: Indicateur
) -> None:
    Reponse.objects.create(entree=entree, indicateur=fatigue, valeur=4)
    with pytest.raises(IntegrityError), transaction.atomic():
        fatigue.delete()


def test_supprimer_une_entree_supprime_ses_reponses(
    entree: EntreeSensations, fatigue: Indicateur
) -> None:
    Reponse.objects.create(entree=entree, indicateur=fatigue, valeur=4)
    entree.delete()
    assert not Reponse.objects.exists()


def test_updated_at_change_sur_une_entree(entree: EntreeSensations) -> None:
    avant = entree.updated_at
    time.sleep(0.01)
    entree.save()
    entree.refresh_from_db()
    assert entree.updated_at > avant
