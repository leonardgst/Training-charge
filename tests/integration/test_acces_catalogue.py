"""Catalogue de Postgres (A1), méta-tests (A2) et index en double.

Le catalogue est lu sous le rôle de migration, propriétaire du schéma.
"""

import os

import psycopg
import pytest
from catalogue_acces import (
    catalogue_des_routes,
    index_en_double,
    objets_trop_ouverts,
    routes_qui_fuient,
)
from django.test import Client, override_settings

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def role_execution() -> str:
    return os.environ["DB_RUNTIME_USER"]


def test_a1_la_base_n_a_aucun_objet_trop_ouvert(
    connexion_migration: psycopg.Connection, role_execution: str
) -> None:
    assert objets_trop_ouverts(connexion_migration, role_execution) == []


def test_aucun_index_en_double(connexion_migration: psycopg.Connection) -> None:
    assert index_en_double(connexion_migration) == []


def _anomalies_apres(
    conn: psycopg.Connection, role_execution: str, instructions: list[str]
) -> list[str]:
    """Exécute les instructions dans une transaction annulée, et relit le catalogue."""
    with conn.transaction():
        for instruction in instructions:
            conn.execute(instruction)
        anomalies = objets_trop_ouverts(conn, role_execution)
        raise psycopg.Rollback
    return anomalies  # pragma: no cover


def test_a2_une_table_accordee_a_public_est_detectee(
    connexion_migration: psycopg.Connection, role_execution: str
) -> None:
    anomalies = _anomalies_apres(
        connexion_migration,
        role_execution,
        ["CREATE TABLE ouverte (id integer)", "GRANT SELECT ON ouverte TO PUBLIC"],
    )
    assert "droit à PUBLIC sur ouverte" in anomalies
    assert objets_trop_ouverts(connexion_migration, role_execution) == []


def test_a2_une_fonction_security_definer_est_detectee(
    connexion_migration: psycopg.Connection, role_execution: str
) -> None:
    anomalies = _anomalies_apres(
        connexion_migration,
        role_execution,
        ["CREATE FUNCTION piege() RETURNS integer LANGUAGE sql SECURITY DEFINER AS 'SELECT 1'"],
    )
    assert "fonction SECURITY DEFINER piege" in anomalies


def test_a2_une_fonction_executable_par_public_est_detectee(
    connexion_migration: psycopg.Connection, role_execution: str
) -> None:
    anomalies = _anomalies_apres(
        connexion_migration,
        role_execution,
        [
            "CREATE FUNCTION ouverte() RETURNS integer LANGUAGE sql AS 'SELECT 1'",
            "GRANT EXECUTE ON FUNCTION ouverte() TO PUBLIC",
        ],
    )
    assert "EXECUTE accordé à PUBLIC sur la fonction ouverte" in anomalies


def test_a2_une_vue_sans_security_invoker_est_detectee(
    connexion_migration: psycopg.Connection, role_execution: str
) -> None:
    anomalies = _anomalies_apres(
        connexion_migration, role_execution, ["CREATE VIEW sans_garde AS SELECT 1 AS un"]
    )
    assert "vue sans security_invoker sans_garde" in anomalies


def test_a2_une_vue_avec_security_invoker_est_acceptee(
    connexion_migration: psycopg.Connection, role_execution: str
) -> None:
    anomalies = _anomalies_apres(
        connexion_migration,
        role_execution,
        ["CREATE VIEW gardee WITH (security_invoker = true) AS SELECT 1 AS un"],
    )
    assert anomalies == []


def test_a2_un_droit_de_creation_du_role_d_execution_est_detecte(
    connexion_migration: psycopg.Connection, role_execution: str
) -> None:
    anomalies = _anomalies_apres(
        connexion_migration,
        role_execution,
        [f'GRANT CREATE ON SCHEMA public TO "{role_execution}"'],
    )
    assert any("peut créer dans le schéma" in a for a in anomalies)


def test_a2_un_droit_de_schema_accorde_a_public_est_detecte(
    connexion_migration: psycopg.Connection, role_execution: str
) -> None:
    anomalies = _anomalies_apres(
        connexion_migration, role_execution, ["GRANT USAGE ON SCHEMA public TO PUBLIC"]
    )
    assert "droit de schéma accordé à PUBLIC" in anomalies


def test_a2_un_index_en_double_est_detecte(connexion_migration: psycopg.Connection) -> None:
    with connexion_migration.transaction():
        connexion_migration.execute("CREATE TABLE doublon (id integer)")
        connexion_migration.execute("CREATE INDEX doublon_a ON doublon (id)")
        connexion_migration.execute("CREATE INDEX doublon_b ON doublon (id)")
        trouves = index_en_double(connexion_migration)
        raise psycopg.Rollback
    assert any("doublon_a, doublon_b" in t for t in trouves)


def test_a2_une_route_publique_oubliee_est_detectee() -> None:
    with override_settings(ROOT_URLCONF="urls_route_ouverte"):
        chemins = catalogue_des_routes("urls_route_ouverte")
        fuites = routes_qui_fuient(Client(), chemins)
    assert "/fuite/" in chemins
    assert "GET /fuite/ -> 200" in fuites
    assert "POST /fuite/ -> 200" in fuites
