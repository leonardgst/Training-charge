"""Sous-agents et skills de Claude Code : format reconnu par Claude Code (ADR-0019).

Un champ mal nommé est ignoré sans avertissement par Claude Code : un sous-agent garderait
alors des outils qu'on croyait lui retirer. Ces tests vérifient l'en-tête de chaque fichier.
"""

from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[2]
AGENTS = sorted((RACINE / ".claude" / "agents").glob("*.md"))
SKILLS = sorted((RACINE / ".claude" / "skills").glob("*/SKILL.md"))

CHAMPS_AGENT = {"name", "description", "tools", "disallowedTools", "model"}
CHAMPS_SKILL = {
    "name",
    "description",
    "argument-hint",
    "disable-model-invocation",
    "context",
    "agent",
}
MODELES = {"opus", "sonnet", "haiku", "inherit"}
OUTILS_INTEGRES = {"Read", "Grep", "Glob", "Bash", "Edit", "Write"}


def en_tete(fichier: Path) -> dict[str, str]:
    """Champs de l'en-tête YAML, une ligne `cle: valeur` chacun.

    Une valeur sans guillemets ne contient ni « : » ni « # » précédé d'une espace : en
    YAML, ils couperaient la valeur, et Claude Code ignorerait l'en-tête.
    """
    lignes = fichier.read_text(encoding="utf-8").splitlines()
    assert lignes[0] == "---", f"{fichier.name} doit commencer par un en-tête ---"
    fin = lignes.index("---", 1)
    champs = {}
    for ligne in lignes[1:fin]:
        cle, separateur, valeur = ligne.partition(":")
        assert separateur, f"ligne d'en-tête illisible dans {fichier}: {ligne!r}"
        valeur = valeur.strip()
        if not valeur.startswith(('"', "'")):
            assert ": " not in valeur and " #" not in valeur, f"{fichier.name}, {cle} : à citer"
        champs[cle.strip()] = valeur
    return champs


def outils(valeur: str) -> list[str]:
    return [outil.strip() for outil in valeur.split(",") if outil.strip()]


def test_les_dossiers_contiennent_des_agents_et_des_skills() -> None:
    assert AGENTS
    assert SKILLS


@pytest.mark.parametrize("fichier", AGENTS, ids=lambda f: f.stem)
def test_un_agent_a_un_en_tete_reconnu(fichier: Path) -> None:
    champs = en_tete(fichier)

    assert set(champs) <= CHAMPS_AGENT
    assert champs["name"] == fichier.stem
    assert champs["description"]
    assert champs["model"] in MODELES


@pytest.mark.parametrize("fichier", AGENTS, ids=lambda f: f.stem)
def test_un_agent_ne_cite_que_des_outils_connus(fichier: Path) -> None:
    champs = en_tete(fichier)
    cites = outils(champs.get("tools", "")) + outils(champs.get("disallowedTools", ""))

    inconnus = [
        outil
        for outil in cites
        if outil not in OUTILS_INTEGRES and not outil.startswith(("mcp__neon__", "mcp__vercel__"))
    ]
    assert inconnus == []


AGENTS_EN_LECTURE = [agent for agent in AGENTS if "disallowedTools" in en_tete(agent)]
SKILLS_DELEGUES = [skill for skill in SKILLS if "agent" in en_tete(skill)]


def test_les_relecteurs_et_le_diagnostic_sont_en_lecture_seule() -> None:
    assert {agent.stem for agent in AGENTS_EN_LECTURE} == {"gardien-acces", "ops", "relecteur"}


@pytest.mark.parametrize("fichier", AGENTS_EN_LECTURE, ids=lambda f: f.stem)
def test_un_agent_en_lecture_seule_n_a_ni_edit_ni_write(fichier: Path) -> None:
    champs = en_tete(fichier)

    assert {"Edit", "Write"} <= set(outils(champs["disallowedTools"]))
    assert not {"Edit", "Write"} & set(outils(champs["tools"]))


@pytest.mark.parametrize("fichier", SKILLS, ids=lambda f: f.parent.name)
def test_un_skill_a_un_en_tete_reconnu(fichier: Path) -> None:
    champs = en_tete(fichier)

    assert set(champs) <= CHAMPS_SKILL
    assert champs["name"] == fichier.parent.name
    assert 0 < len(champs["description"]) <= 1536


@pytest.mark.parametrize("fichier", SKILLS_DELEGUES, ids=lambda f: f.parent.name)
def test_un_skill_delegue_a_un_agent_qui_existe(fichier: Path) -> None:
    champs = en_tete(fichier)

    assert champs["context"] == "fork"
    assert champs["agent"] in {agent.stem for agent in AGENTS}
