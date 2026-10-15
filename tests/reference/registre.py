"""Registre des cas C1 à C15 et marques `xfail` des tests du moteur.

Les tests du moteur sont introduits avant son implémentation (phase 3) : chacun est en
`xfail(strict=True)` jusqu'à la PR qui fait passer son cas, et cette PR retire la ligne
correspondante de `PR_PREVUE`. Un cas qui passe alors qu'il est encore marqué fait échouer
la CI, ce qui oblige à retirer la marque.
"""

import pytest

# Cas -> PR de la phase 3 qui doit le faire passer (fiche de la phase 3, table des PR).
PR_PREVUE: dict[str, str] = {
    "C01": "3.2",
    "C02": "3.2",
    "C03": "3.3",
    "C04": "3.4",
    "C05": "3.2",
    "C06": "3.4",
    "C07": "3.5",  # intensité en 3.4, sensations en 3.5
    "C08": "3.5",  # intensité en 3.4, sensations en 3.5
    "C09": "3.3",
    "C10": "3.2",
    "C11": "3.5",
    "C12": "3.5",
    "C13": "3.5",
    "C14": "3.4",
    "C15": "3.5",
}
CAS = tuple(f"C{numero:02d}" for numero in range(1, 16))

# Seules ces exceptions signalent « pas encore écrit » ; tout autre échec (erreur du
# harnais, par exemple) reste un échec franc.
ATTENDUES = (NotImplementedError, AssertionError, FileNotFoundError)


def marque_xfail(cas: str) -> pytest.MarkDecorator:
    return pytest.mark.xfail(
        reason=f"moteur non écrit (PR {PR_PREVUE[cas]}) ou dossier du mainteneur absent",
        raises=ATTENDUES,
        strict=True,
    )


def parametres_des_cas() -> list[object]:
    return [
        pytest.param(cas, marks=marque_xfail(cas) if cas in PR_PREVUE else (), id=cas)
        for cas in CAS
    ]
