"""Garde-fous de Claude Code : hook des plateformes et réglages versionnés (ADR-0019).

Le hook décide pour chaque appel aux serveurs MCP de Neon et de Vercel ; les réglages fixent
ce que Claude fait seul, ce qu'il demande et ce qui lui est refusé. Ces tests empêchent
qu'une modification les assouplisse sans qu'un test change dans la même PR.
"""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

RACINE = Path(__file__).resolve().parents[2]
HOOK = RACINE / ".claude" / "hooks" / "garde_plateformes.py"
REGLAGES = RACINE / ".claude" / "settings.json"
SERVEURS_MCP = RACINE / ".mcp.json"

PRODUCTION = "br-production-0001"
TRAVAIL = "br-travail-0002"
PROTEGEES = frozenset({"production", PRODUCTION})


def _charger_hook() -> ModuleType:
    spec = importlib.util.spec_from_file_location("garde_plateformes", HOOK)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


garde = _charger_hook()


def _appel(outil: str, **entree: Any) -> dict[str, Any]:
    return {"hook_event_name": "PreToolUse", "tool_name": outil, "tool_input": entree}


def _nature(decision: dict[str, str] | None) -> str | None:
    return None if decision is None else decision["permissionDecision"]


# Neon


@pytest.mark.parametrize("outil", sorted(garde.NEON_LECTURE))
def test_neon_la_lecture_passe_sans_decision(outil: str) -> None:
    assert garde.decider(_appel(f"mcp__neon__{outil}"), PROTEGEES) is None


def test_neon_creer_une_branche_de_travail_passe_sans_decision() -> None:
    appel = _appel("mcp__neon__create_branch", project_id="p", name="essai")

    assert garde.decider(appel, PROTEGEES) is None


@pytest.mark.parametrize("outil", ["run_sql", "run_sql_transaction", "delete_branch"])
def test_neon_ecrire_sur_une_branche_de_travail_passe_sans_decision(outil: str) -> None:
    appel = _appel(f"mcp__neon__{outil}", branch_id=TRAVAIL)

    assert garde.decider(appel, PROTEGEES) is None


@pytest.mark.parametrize("branche", [PRODUCTION, "production"])
def test_neon_le_sql_sur_la_production_demande_l_accord(branche: str) -> None:
    appel = _appel("mcp__neon__run_sql", branch_id=branche, sql="SELECT 1")

    assert _nature(garde.decider(appel, PROTEGEES)) == "ask"


@pytest.mark.parametrize("outil", ["delete_branch", "reset_from_parent"])
def test_neon_supprimer_ou_reinitialiser_la_production_est_refuse(outil: str) -> None:
    appel = _appel(f"mcp__neon__{outil}", branch_id=PRODUCTION)

    assert _nature(garde.decider(appel, PROTEGEES)) == "deny"


def test_neon_l_identifiant_en_camelcase_est_aussi_reconnu() -> None:
    appel = _appel("mcp__neon__delete_branch", branchId=PRODUCTION)

    assert _nature(garde.decider(appel, PROTEGEES)) == "deny"


def test_neon_une_branche_non_precisee_demande_l_accord() -> None:
    appel = _appel("mcp__neon__run_sql", sql="DELETE FROM joueur")

    assert _nature(garde.decider(appel, PROTEGEES)) == "ask"


def test_neon_sans_identifiant_de_production_toute_ecriture_demande_l_accord() -> None:
    appel = _appel("mcp__neon__run_sql", branch_id=TRAVAIL, sql="SELECT 1")

    assert _nature(garde.decider(appel, frozenset({"production"}))) == "ask"


def test_neon_un_outil_inconnu_demande_l_accord() -> None:
    appel = _appel("mcp__neon__update_postgres_endpoint", branch_id=TRAVAIL)

    assert _nature(garde.decider(appel, PROTEGEES)) == "ask"


# Vercel et autres outils


@pytest.mark.parametrize("outil", sorted(garde.VERCEL_LECTURE))
def test_vercel_la_lecture_passe_sans_decision(outil: str) -> None:
    assert garde.decider(_appel(f"mcp__vercel__{outil}"), PROTEGEES) is None


def test_vercel_tout_autre_outil_demande_l_accord() -> None:
    appel = _appel("mcp__vercel__deploy_to_vercel", project="u19-load-tracking")

    assert _nature(garde.decider(appel, PROTEGEES)) == "ask"


def test_un_outil_hors_neon_et_vercel_passe_sans_decision() -> None:
    assert garde.decider(_appel("Bash", command="git status"), PROTEGEES) is None


# Fichier des branches protégées


def test_le_fichier_versionne_protege_la_branche_production() -> None:
    assert "production" in garde.branches_protegees()


def test_un_fichier_de_branches_illisible_ne_protege_rien_de_plus(tmp_path: Path) -> None:
    fichier = tmp_path / "branches.json"
    fichier.write_text("pas du JSON", encoding="utf-8")

    assert garde.branches_protegees(fichier) == frozenset()


# Script lancé comme par Claude Code


def _lancer(entree: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603
        [sys.executable, str(HOOK)],
        input=entree,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )


def test_le_script_ecrit_la_decision_au_format_de_claude_code() -> None:
    resultat = _lancer(json.dumps(_appel("mcp__vercel__deploy_to_vercel")))

    assert resultat.returncode == 0
    sortie = json.loads(resultat.stdout)["hookSpecificOutput"]
    assert sortie["hookEventName"] == "PreToolUse"
    assert sortie["permissionDecision"] == "ask"


def test_le_script_ne_dit_rien_quand_il_n_a_pas_de_decision() -> None:
    resultat = _lancer(json.dumps(_appel("mcp__neon__list_branches")))

    assert (resultat.returncode, resultat.stdout) == (0, "")


def test_le_script_bloque_un_appel_illisible() -> None:
    assert _lancer("pas du JSON").returncode == 2


# Réglages versionnés


def _reglages() -> dict[str, Any]:
    return json.loads(REGLAGES.read_text(encoding="utf-8"))


def test_les_reglages_gardent_le_mode_auto_sans_contournement() -> None:
    permissions = _reglages()["permissions"]

    assert permissions["defaultMode"] == "auto"
    assert permissions["disableBypassPermissionsMode"] == "disable"


def test_la_fusion_d_une_pr_demande_l_accord_du_mainteneur() -> None:
    permissions = _reglages()["permissions"]

    assert "Bash(gh pr merge *)" in permissions["ask"]
    assert not any("gh pr merge" in regle for regle in permissions["allow"])


@pytest.mark.parametrize(
    "regle",
    [
        "Read(./.env)",
        "Edit(/.claude/settings.json)",
        "Edit(/.claude/hooks/**)",
        "Edit(/.mcp.json)",
        "Edit(/tests/reference/**/attendu.csv)",
        "Bash(git push *--force*)",
        "Bash(git push origin main*)",
        "Bash(gh auth *)",
        "Bash(gh secret *)",
        "Bash(vercel *)",
        "Bash(neonctl *)",
        "mcp__neon__complete_database_migration",
        "mcp__neon__delete_project",
        "mcp__neon__rotate_credential",
    ],
)
def test_les_refus_essentiels_sont_presents(regle: str) -> None:
    assert regle in _reglages()["permissions"]["deny"]


def test_aucune_regle_n_autorise_un_outil_mcp_en_bloc() -> None:
    autorisations = _reglages()["permissions"]["allow"]

    assert [regle for regle in autorisations if regle.startswith("mcp__") and "*" in regle] == []


def test_le_hook_des_plateformes_est_branche_sur_neon_et_vercel() -> None:
    (groupe,) = _reglages()["hooks"]["PreToolUse"]
    (commande,) = groupe["hooks"]

    assert groupe["matcher"] == "^mcp__(neon|vercel)__"
    assert commande["args"] == ["${CLAUDE_PROJECT_DIR}/.claude/hooks/garde_plateformes.py"]
    assert HOOK.is_file()


def test_les_serveurs_mcp_sont_les_serveurs_officiels() -> None:
    serveurs = json.loads(SERVEURS_MCP.read_text(encoding="utf-8"))["mcpServers"]

    assert serveurs == {
        "neon": {"type": "http", "url": "https://mcp.neon.tech/mcp?projectId=${NEON_PROJECT_ID}"},
        "vercel": {"type": "http", "url": "https://mcp.vercel.com"},
    }
