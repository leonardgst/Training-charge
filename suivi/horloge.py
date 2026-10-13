"""Date du jour : fonction unique du projet.

Aucun autre module n'appelle `date.today()` ni ne lit l'heure pour en tirer la date ;
les tests remplacent cette fonction par une date fixe.
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo

FUSEAU = ZoneInfo("Europe/Paris")


def aujourd_hui() -> date:
    """Date du jour à l'heure de Paris."""
    return datetime.now(FUSEAU).date()
