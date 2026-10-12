"""Fixtures d'intégration : connexions directes à la base de test, sous chaque rôle.

La base de test est créée par `pytest-django` avec le rôle de migration, puis migrée
depuis zéro. Le rôle d'exécution s'y connecte comme le ferait l'application déployée.
"""

import os
from collections.abc import Iterator

import psycopg
import pytest
from django.db import connection


def _connecter(utilisateur: str, mot_de_passe: str) -> psycopg.Connection:
    reglages = connection.settings_dict
    return psycopg.connect(
        dbname=reglages["NAME"],
        user=utilisateur,
        password=mot_de_passe,
        host=reglages["HOST"],
        port=reglages["PORT"],
        autocommit=True,
    )


@pytest.fixture
def connexion_migration(transactional_db: None) -> Iterator[psycopg.Connection]:
    reglages = connection.settings_dict
    with _connecter(reglages["USER"], reglages["PASSWORD"]) as conn:
        yield conn


@pytest.fixture
def connexion_execution(transactional_db: None) -> Iterator[psycopg.Connection]:
    with _connecter(os.environ["DB_RUNTIME_USER"], os.environ["DB_RUNTIME_PASSWORD"]) as conn:
        yield conn
