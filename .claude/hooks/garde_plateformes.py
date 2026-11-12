"""Garde des serveurs MCP de Neon et de Vercel (ADR-0019).

Hook `PreToolUse` de Claude Code : il lit l'appel d'outil en JSON sur l'entrée standard et
répond, s'il y a lieu, par une décision JSON sur la sortie standard. Les règles de
`.claude/settings.json` s'appliquent en plus : ce hook peut refuser un appel ou faire
demander l'accord du mainteneur, jamais lever un refus.

- Neon : lecture libre ; écriture libre sur une branche de travail ; SQL sur une branche
  protégée soumis à l'accord du mainteneur ; suppression ou réinitialisation d'une branche
  protégée refusée ; accord demandé si la branche n'est pas précisée ou si l'outil est inconnu.
- Vercel : lecture libre ; tout autre outil demande l'accord du mainteneur.

Bibliothèque standard seulement : le hook tourne avec le `python3` du système, hors de uv.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

FICHIER_BRANCHES_PROTEGEES = Path(__file__).with_name("neon-branches-protegees.json")

PREFIXE_NEON = "mcp__neon__"
PREFIXE_VERCEL = "mcp__vercel__"

# Outils Neon sans effet sur les données ni sur la configuration.
NEON_LECTURE = frozenset(
    {
        "compare_database_schema",
        "describe_branch",
        "describe_project",
        "describe_table_schema",
        "explain_sql_statement",
        "fetch",
        "get_database_tables",
        "get_doc",
        "inspect_database",
        "list_branch_computes",
        "list_branches",
        "list_organizations",
        "list_projects",
        "list_slow_queries",
        "search",
        "search_docs",
    }
)

# Outils Neon qui créent une branche temporaire sans modifier la branche d'origine.
NEON_SANS_RISQUE = frozenset(
    {"create_branch", "prepare_database_migration", "prepare_query_tuning"}
)

# Outils Neon qui agissent sur la branche désignée par `branch_id`.
NEON_SQL = frozenset({"run_sql", "run_sql_transaction"})
NEON_DESTRUCTIFS = frozenset({"delete_branch", "reset_from_parent"})

# Outils Vercel en lecture seule (catalogue de Vercel MCP, outils les plus utilisés).
VERCEL_LECTURE = frozenset(
    {
        "get_active_attack_status",
        "get_alias",
        "get_deployment",
        "get_git_deployment_context",
        "get_project",
        "get_project_domain",
        "get_runtime_errors",
        "get_runtime_logs",
        "get_team",
        "list_aliases",
        "list_deployment_aliases",
        "list_deployment_events",
        "list_deployment_files",
        "list_deployments",
        "list_project_custom_environments",
        "list_project_domains",
        "list_projects",
        "list_teams",
        "search_vercel_documentation",
        "web_fetch_vercel_url",
    }
)


def _decision(nature: str, raison: str) -> dict[str, str]:
    return {
        "hookEventName": "PreToolUse",
        "permissionDecision": nature,
        "permissionDecisionReason": raison,
    }


def branches_protegees(fichier: Path = FICHIER_BRANCHES_PROTEGEES) -> frozenset[str]:
    """Noms et identifiants des branches Neon protégées ; vide si le fichier est illisible."""
    try:
        donnees = json.loads(fichier.read_text(encoding="utf-8"))
        return frozenset(str(branche) for branche in donnees["branches"])
    except (OSError, ValueError, KeyError, TypeError):
        return frozenset()


def _decision_neon(
    outil: str, entree: dict[str, Any], protegees: frozenset[str]
) -> dict[str, str] | None:
    if outil in NEON_LECTURE or outil in NEON_SANS_RISQUE:
        return None
    if outil not in NEON_SQL and outil not in NEON_DESTRUCTIFS:
        return _decision("ask", f"Outil Neon « {outil} » hors des listes connues du hook.")

    branche = entree.get("branch_id") or entree.get("branchId")
    if not branche:
        return _decision(
            "ask", "Branche Neon non précisée : Neon prendrait la branche par défaut, production."
        )
    if not any(nom.startswith("br-") for nom in protegees):
        return _decision(
            "ask",
            "Identifiant de la branche production absent de "
            ".claude/hooks/neon-branches-protegees.json : branche non vérifiable.",
        )
    if branche not in protegees:
        return None
    if outil in NEON_DESTRUCTIFS:
        return _decision("deny", f"« {outil} » sur une branche Neon protégée est interdit.")
    return _decision("ask", "SQL sur une branche Neon protégée : accord du mainteneur requis.")


def _decision_vercel(outil: str) -> dict[str, str] | None:
    if outil in VERCEL_LECTURE:
        return None
    return _decision(
        "ask",
        f"Outil Vercel « {outil} » : il peut modifier un projet, un déploiement ou une variable.",
    )


def decider(appel: dict[str, Any], protegees: frozenset[str]) -> dict[str, str] | None:
    """Décision du hook pour un appel d'outil, ou None pour le circuit d'autorisation normal."""
    nom = str(appel.get("tool_name", ""))
    entree = appel.get("tool_input")
    if not isinstance(entree, dict):
        entree = {}
    if nom.startswith(PREFIXE_NEON):
        return _decision_neon(nom[len(PREFIXE_NEON) :], entree, protegees)
    if nom.startswith(PREFIXE_VERCEL):
        return _decision_vercel(nom[len(PREFIXE_VERCEL) :])
    return None


def main() -> int:
    try:
        appel = json.load(sys.stdin)
    except ValueError:
        print("Appel d'outil illisible : refusé par précaution.", file=sys.stderr)
        return 2
    if not isinstance(appel, dict):
        print("Appel d'outil inattendu : refusé par précaution.", file=sys.stderr)
        return 2
    decision = decider(appel, branches_protegees())
    if decision is not None:
        json.dump({"hookSpecificOutput": decision}, sys.stdout, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
