"""Journal : le jeton d'un lien joueur n'y figure jamais (ADR-0006, CLAUDE.md, section 10).

Django journalise l'adresse de chaque réponse 404 ou 403 (`django.request`) ; celle du
questionnaire contient le jeton, y compris celui d'un lien révoqué ou mal recopié.
"""

import logging
import re

ADRESSE_AVEC_JETON = re.compile(r"/q/[^/\s?#]+")
REMPLACEMENT = "/q/[jeton]"


def _masquer(valeur: object) -> object:
    return ADRESSE_AVEC_JETON.sub(REMPLACEMENT, valeur) if isinstance(valeur, str) else valeur


class MasqueLeJeton(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = _masquer(record.msg)
        if isinstance(record.args, tuple):
            record.args = tuple(_masquer(argument) for argument in record.args)
        elif isinstance(record.args, dict):
            record.args = {cle: _masquer(valeur) for cle, valeur in record.args.items()}
        return True
