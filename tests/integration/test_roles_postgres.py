"""Migrations depuis zéro et rôles Postgres (cas D3 et squelette de A1).

Ces tests interrogent le catalogue d'une vraie base ; aucun simulacre.
"""

import os

import psycopg
import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

pytestmark = pytest.mark.django_db(transaction=True)


def test_migrations_depuis_zero_sans_reste_a_appliquer() -> None:
    executor = MigrationExecutor(connection)
    assert executor.migration_plan(executor.loader.graph.leaf_nodes()) == []
    with connection.cursor() as curseur:
        curseur.execute("SELECT count(*) FROM django_migrations")
        assert curseur.fetchone()[0] > 0


def test_role_d_execution_ne_peut_pas_creer_dans_le_schema(
    connexion_execution: psycopg.Connection,
) -> None:
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        connexion_execution.execute("CREATE TABLE intrus (id integer)")


def test_role_d_execution_ne_peut_pas_modifier_le_schema_existant(
    connexion_execution: psycopg.Connection,
) -> None:
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        connexion_execution.execute("ALTER TABLE django_migrations ADD COLUMN intrus integer")
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        connexion_execution.execute("DROP TABLE django_migrations")


def test_role_d_execution_a_les_droits_par_defaut_sur_une_nouvelle_table(
    connexion_migration: psycopg.Connection,
    connexion_execution: psycopg.Connection,
) -> None:
    connexion_migration.execute("CREATE TABLE essai_droits (id serial PRIMARY KEY, nom text)")
    try:
        connexion_execution.execute("INSERT INTO essai_droits (nom) VALUES ('a')")
        connexion_execution.execute("UPDATE essai_droits SET nom = 'b'")
        ligne = connexion_execution.execute("SELECT nom FROM essai_droits").fetchone()
        assert ligne == ("b",)
        connexion_execution.execute("DELETE FROM essai_droits")
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            connexion_execution.execute("TRUNCATE essai_droits")
    finally:
        connexion_migration.execute("DROP TABLE essai_droits")


def test_aucun_droit_accorde_a_public(connexion_migration: psycopg.Connection) -> None:
    tables = connexion_migration.execute(
        """
        SELECT table_name, privilege_type FROM information_schema.role_table_grants
        WHERE grantee = 'PUBLIC' AND table_schema = 'public'
        """
    ).fetchall()
    assert tables == []

    schema = connexion_migration.execute(
        """
        SELECT has_schema_privilege('public', 'public', 'USAGE'),
               has_schema_privilege('public', 'public', 'CREATE')
        """
    ).fetchone()
    assert schema == (False, False)

    fonctions = connexion_migration.execute(
        """
        SELECT p.proname FROM pg_proc p
        JOIN pg_namespace n ON n.oid = p.pronamespace
        WHERE n.nspname = 'public'
          AND EXISTS (
            SELECT 1 FROM aclexplode(coalesce(p.proacl, acldefault('f', p.proowner))) a
            WHERE a.grantee = 0
          )
        """
    ).fetchall()
    assert fonctions == []


def test_acl_de_la_base_sans_public(connexion_migration: psycopg.Connection) -> None:
    acl = connexion_migration.execute(
        """
        SELECT a.privilege_type
        FROM pg_database d,
             aclexplode(coalesce(d.datacl, acldefault('d', d.datdba))) a
        WHERE d.datname = %s AND a.grantee = 0
        """,
        [_base_de_developpement()],
    ).fetchall()
    assert acl == []


def test_aucune_fonction_security_definer(connexion_migration: psycopg.Connection) -> None:
    fonctions = connexion_migration.execute(
        """
        SELECT p.proname FROM pg_proc p
        JOIN pg_namespace n ON n.oid = p.pronamespace
        WHERE p.prosecdef AND n.nspname = 'public'
        """
    ).fetchall()
    assert fonctions == []


def _base_de_developpement() -> str:
    return os.environ["DB_NAME"]
