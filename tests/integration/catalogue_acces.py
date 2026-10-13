"""Vérifications de A1, partagées avec les méta-tests de A2.

Deux catalogues : celui des routes (résolveur d'URL de Django) et celui de Postgres.
Chaque fonction renvoie la liste des anomalies, vide quand tout est fermé ; A1 exige une
liste vide, A2 prouve que ces fonctions détectent bien une anomalie introduite exprès.
"""

import re

import psycopg
from django.test import Client
from django.urls import URLPattern, URLResolver, get_resolver

# Routes publiques voulues (ADR-0005) : connexion, contrôle de santé, connexion de l'admin.
LISTE_BLANCHE = {"/connexion/", "/sante/", "/admin/login/"}


def _routes(motifs: list, prefixe: str = "") -> list[str]:
    chemins: list[str] = []
    for motif in motifs:
        if isinstance(motif, URLResolver):
            chemins += _routes(motif.url_patterns, prefixe + str(motif.pattern))
        elif isinstance(motif, URLPattern):
            chemins.append(prefixe + str(motif.pattern))
    return chemins


def _chemin_concret(motif: str) -> str:
    """Remplace chaque paramètre du motif par une valeur plausible."""
    chemin = re.sub(r"<(?:int:)?[^>]*(?:id|pk|object_id)>", "1", motif)
    chemin = re.sub(r"<[^>]+>", "x", chemin)
    return "/" + chemin.removeprefix("^").removesuffix("$")


def catalogue_des_routes(urlconf: str | None = None) -> list[str]:
    """Tous les chemins du résolveur, hors liste blanche."""
    motifs = get_resolver(urlconf).url_patterns
    return sorted({_chemin_concret(m) for m in _routes(motifs)} - LISTE_BLANCHE)


def routes_qui_fuient(client: Client, chemins: list[str]) -> list[str]:
    """Routes qui répondent autre chose qu'un refus ou une redirection vers la connexion."""
    fuites: list[str] = []
    for chemin in chemins:
        for methode in ("get", "post"):
            reponse = getattr(client, methode)(chemin)
            if reponse.status_code in {401, 403, 404}:
                continue
            if reponse.status_code in {301, 302} and (
                "/login/" in reponse["Location"] or "/connexion/" in reponse["Location"]
            ):
                continue
            fuites.append(f"{methode.upper()} {chemin} -> {reponse.status_code}")
    return fuites


def objets_trop_ouverts(conn: psycopg.Connection, role_execution: str) -> list[str]:
    """Droits de `PUBLIC`, fonctions `SECURITY DEFINER`, vues sans `security_invoker`,
    droit de créer dans le schéma pour le rôle d'exécution."""
    anomalies: list[str] = []

    def lignes(requete: str, parametres: tuple = ()) -> list[str]:
        return [ligne[0] for ligne in conn.execute(requete, parametres).fetchall()]

    anomalies += [
        f"droit à PUBLIC sur {nom}"
        for nom in lignes(
            """
            SELECT c.relname FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            CROSS JOIN LATERAL aclexplode(c.relacl) a
            WHERE n.nspname = 'public' AND a.grantee = 0
              AND c.relkind IN ('r', 'p', 'v', 'm', 'S', 'f')
            """
        )
    ]
    # `proacl` nul = droits par défaut, dont EXECUTE pour PUBLIC.
    anomalies += [
        f"EXECUTE accordé à PUBLIC sur la fonction {nom}"
        for nom in lignes(
            """
            SELECT p.proname FROM pg_proc p
            JOIN pg_namespace n ON n.oid = p.pronamespace
            WHERE n.nspname = 'public' AND (
              p.proacl IS NULL OR EXISTS (
                SELECT 1 FROM aclexplode(p.proacl) a
                WHERE a.grantee = 0 AND a.privilege_type = 'EXECUTE'))
            """
        )
    ]
    anomalies += [
        f"fonction SECURITY DEFINER {nom}"
        for nom in lignes(
            """
            SELECT p.proname FROM pg_proc p
            JOIN pg_namespace n ON n.oid = p.pronamespace
            WHERE n.nspname = 'public' AND p.prosecdef
            """
        )
    ]
    anomalies += [
        f"vue sans security_invoker {nom}"
        for nom in lignes(
            """
            SELECT c.relname FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND c.relkind IN ('v', 'm')
              AND NOT COALESCE('security_invoker=true' = ANY (c.reloptions), false)
            """
        )
    ]
    anomalies += [
        "droit de schéma accordé à PUBLIC"
        for _ in lignes(
            """
            SELECT 1 FROM pg_namespace n CROSS JOIN LATERAL aclexplode(n.nspacl) a
            WHERE n.nspname = 'public' AND a.grantee = 0
            """
        )
    ]
    anomalies += [
        f"le rôle d'exécution peut créer dans le schéma ({role})"
        for role in lignes(
            "SELECT %s WHERE has_schema_privilege(%s, 'public', 'CREATE')",
            (role_execution, role_execution),
        )
    ]
    return anomalies


def index_en_double(conn: psycopg.Connection) -> list[str]:
    """Index du schéma `public` qui portent sur les mêmes colonnes, avec les mêmes options."""
    lignes = conn.execute(
        """
        SELECT i.indrelid::regclass::text, string_agg(c.relname, ', ' ORDER BY c.relname)
        FROM pg_index i
        JOIN pg_class c ON c.oid = i.indexrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public'
        GROUP BY i.indrelid, i.indkey::text, i.indclass::text, i.indcollation::text,
                 i.indoption::text, i.indisunique,
                 coalesce(pg_get_expr(i.indexprs, i.indrelid), ''),
                 coalesce(pg_get_expr(i.indpred, i.indrelid), '')
        HAVING count(*) > 1
        """
    ).fetchall()
    return [f"{table} : {noms}" for table, noms in lignes]
