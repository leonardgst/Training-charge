"""Journal : le jeton d'un lien joueur n'y figure jamais (ADR-0006, CLAUDE.md, section 10).

Django journalise l'adresse de chaque réponse 4xx, refus CSRF et requête du serveur de
développement ; celle du questionnaire contient le jeton, y compris celui d'un lien
révoqué ou mal recopié.
"""

import logging
import re
import sys

ADRESSE_AVEC_JETON = re.compile(r"/q/[^/\s?#]+")
REMPLACEMENT = "/q/[jeton]"


def _masquer(valeur: object) -> object:
    return ADRESSE_AVEC_JETON.sub(REMPLACEMENT, valeur) if isinstance(valeur, str) else valeur


# Journaux de Django qui écrivent l'adresse demandée : réponses 4xx (`django.request`), refus
# CSRF (`django.security.csrf`) et serveur de développement (`django.server`).
JOURNAUX = ("django.request", "django.security.csrf", "django.server")


class MasqueLeJeton(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = _masquer(record.msg)
        if isinstance(record.args, tuple):
            record.args = tuple(_masquer(argument) for argument in record.args)
        elif isinstance(record.args, dict):
            record.args = {cle: _masquer(valeur) for cle, valeur in record.args.items()}
        return True


def masquer_le_jeton_des_journaux() -> None:
    """Pose le filtre sur chaque journal de `JOURNAUX`, une seule fois (appelé au démarrage).

    Un filtre de journal ne s'applique pas aux messages venus de ses enfants : chaque
    journal est donc nommé. Pas de `LOGGING` : sa configuration non incrémentale retirerait
    leurs gestionnaires à ces journaux.
    """
    for nom in JOURNAUX:
        journal = logging.getLogger(nom)
        if not any(isinstance(f, MasqueLeJeton) for f in journal.filters):
            journal.addFilter(MasqueLeJeton())


def configurer_journal_audit() -> None:
    """Rend lisible le journal `suivi.audit` (suppressions d'entrées), une seule fois.

    Sans configuration, Django n'a aucun gestionnaire au niveau racine et le niveau effectif
    serait `WARNING` : la trace serait perdue. Elle va sur la sortie standard, que
    l'hébergeur collecte.
    """
    journal = logging.getLogger("suivi.audit")
    journal.setLevel(logging.INFO)
    if not journal.handlers:
        gestionnaire = logging.StreamHandler(sys.stdout)
        gestionnaire.setFormatter(logging.Formatter("%(asctime)s %(name)s %(message)s"))
        journal.addHandler(gestionnaire)
