"""Actions des workflows épinglées par empreinte de commit (phase 4 bis, PR 4b.3).

Un tag comme `v4` peut être déplacé par l'éditeur de l'action : le code exécuté en CI, avec
les secrets des previews et de la production, changerait sans passer par une PR. Une
empreinte de commit ne bouge pas ; Dependabot propose ses mises à jour.
"""

import re
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
WORKFLOWS = sorted((RACINE / ".github" / "workflows").glob("*.yml"))
USES = re.compile(r"^\s*(?:-\s+)?uses:\s*(?P<action>\S+)(?P<suite>.*)$")
EPINGLEE = re.compile(r"^[\w.-]+/[\w./-]+@[0-9a-f]{40}$")
VERSION = re.compile(r"^\s+# v?\d+(\.\d+)*$")


def actions_utilisees() -> list[tuple[str, str, str]]:
    """(fichier, action, suite de la ligne) pour chaque `uses:` des workflows."""
    trouvees = []
    for fichier in WORKFLOWS:
        for ligne in fichier.read_text(encoding="utf-8").splitlines():
            if correspondance := USES.match(ligne):
                trouvees.append((fichier.name, correspondance["action"], correspondance["suite"]))
    return trouvees


def test_les_workflows_utilisent_des_actions() -> None:
    assert len(WORKFLOWS) >= 3
    assert actions_utilisees()


def test_chaque_action_est_epinglee_par_empreinte_avec_sa_version() -> None:
    mal_epinglees = [
        f"{fichier}: {action}{suite}"
        for fichier, action, suite in actions_utilisees()
        if not action.startswith("./") and not (EPINGLEE.match(action) and VERSION.match(suite))
    ]

    assert mal_epinglees == []


def test_dependabot_met_a_jour_les_actions_epinglees() -> None:
    configuration = (RACINE / ".github" / "dependabot.yml").read_text(encoding="utf-8")

    assert re.search(r"^\s*- package-ecosystem: github-actions$", configuration, re.M)
