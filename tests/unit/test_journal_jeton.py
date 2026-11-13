"""Le jeton d'un lien joueur est masqué dans les enregistrements du journal (ADR-0006)."""

import logging

from suivi.journal import MasqueLeJeton


def _enregistrement(msg: str, args: tuple[object, ...]) -> logging.LogRecord:
    return logging.LogRecord("django.request", logging.WARNING, __file__, 1, msg, args, None)


def test_l_adresse_du_questionnaire_est_masquee_dans_les_arguments() -> None:
    enregistrement = _enregistrement("%s: %s", ("Not Found", "/q/abcDEF_-123"))

    assert MasqueLeJeton().filter(enregistrement) is True
    assert enregistrement.getMessage() == "Not Found: /q/[jeton]"


def test_l_adresse_est_masquee_dans_le_message_et_avec_une_barre_finale() -> None:
    enregistrement = _enregistrement("Not Found: /q/abcDEF/", ())

    MasqueLeJeton().filter(enregistrement)

    assert enregistrement.getMessage() == "Not Found: /q/[jeton]/"


def test_les_arguments_nommes_sont_masques() -> None:
    enregistrement = _enregistrement("%(chemin)s", ({"chemin": "/q/secret?a=1"},))

    MasqueLeJeton().filter(enregistrement)

    assert enregistrement.getMessage() == "/q/[jeton]?a=1"


def test_les_autres_adresses_sont_laissees_telles_quelles() -> None:
    enregistrement = _enregistrement("%s", ("/joueurs/12/",))

    MasqueLeJeton().filter(enregistrement)

    assert enregistrement.getMessage() == "/joueurs/12/"


def test_le_filtre_est_pose_une_seule_fois_sur_les_journaux_de_django() -> None:
    from suivi.journal import JOURNAUX, masquer_le_jeton_des_journaux

    masquer_le_jeton_des_journaux()
    masquer_le_jeton_des_journaux()

    for nom in JOURNAUX:
        assert sum(isinstance(f, MasqueLeJeton) for f in logging.getLogger(nom).filters) == 1
