"""État du questionnaire d'un joueur à la date d'une séance (R22, ADR-0017)."""

import datetime

from suivi.questionnaire import etat_questionnaire

JEUDI = datetime.date(2026, 10, 15)
TOUS = list(range(7))


def test_recu_si_une_entree_existe_quel_que_soit_le_jour() -> None:
    assert etat_questionnaire(JEUDI, JEUDI, [0], recu=True) == "recu"


def test_manquant_un_jour_de_questionnaire_sans_entree() -> None:
    assert etat_questionnaire(JEUDI, JEUDI, TOUS, recu=False) == "manquant"
    assert (
        etat_questionnaire(JEUDI, JEUDI + datetime.timedelta(days=3), [3], recu=False) == "manquant"
    )


def test_rien_un_jour_hors_questionnaire() -> None:
    assert etat_questionnaire(JEUDI, JEUDI, [0, 1, 2], recu=False) is None
    assert etat_questionnaire(JEUDI, JEUDI, [], recu=False) is None


def test_rien_pour_un_jour_qui_n_est_pas_encore_arrive() -> None:
    veille = JEUDI - datetime.timedelta(days=1)
    assert etat_questionnaire(JEUDI, veille, TOUS, recu=False) is None
