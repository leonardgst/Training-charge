"""Adaptateur entre la base et le moteur de calcul.

Seul code qui lit la base pour le moteur. Il ne charge que les participations des séances
validées (les brouillons n'entrent dans aucun calcul) et les données datées au plus tard
de la date de calcul (C9).
"""

import datetime
import tomllib
from functools import cache
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

from engine.charge import calendrier, charges_glissantes
from engine.modeles import ChargesGlissantes, JourCalcule, Parametres, ParticipationValidee
from suivi.models import Participation, StatutSeance

CHEMIN_PARAMETRES = Path(__file__).resolve().parent.parent / "config" / "calcul.toml"


def lire_parametres(chemin: Path = CHEMIN_PARAMETRES) -> Parametres:
    """Lit et valide `config/calcul.toml` ; toute anomalie interrompt le démarrage."""
    with chemin.open("rb") as fichier:
        brut = tomllib.load(fichier)
    entiers = ("fenetre_courte_jours", "fenetre_longue_jours")
    attendues = {"facteur_echelle_charge", *entiers}
    if set(brut) != attendues:
        raise ImproperlyConfigured(f"{chemin.name} : clés attendues {sorted(attendues)}")
    facteur = brut["facteur_echelle_charge"]
    if isinstance(facteur, bool) or not isinstance(facteur, int | float) or facteur <= 0:
        raise ImproperlyConfigured(f"{chemin.name} : facteur_echelle_charge doit être positif")
    for cle in entiers:
        if isinstance(brut[cle], bool) or not isinstance(brut[cle], int) or brut[cle] < 1:
            raise ImproperlyConfigured(f"{chemin.name} : {cle} doit être un entier d'au moins 1")
    if brut["fenetre_courte_jours"] >= brut["fenetre_longue_jours"]:
        raise ImproperlyConfigured(
            f"{chemin.name} : fenetre_courte_jours doit être inférieure à fenetre_longue_jours"
        )
    return Parametres(
        facteur_echelle_charge=float(facteur),
        fenetre_courte_jours=brut["fenetre_courte_jours"],
        fenetre_longue_jours=brut["fenetre_longue_jours"],
    )


@cache
def parametres() -> Parametres:
    return lire_parametres()


def calculer_joueur(
    joueur_id: int, date_calcul: datetime.date, parametres: Parametres
) -> list[JourCalcule]:
    """Calendrier calculé d'un joueur, de sa première participation validée à `date_calcul`."""
    participations = []
    for jour, duree, *rpe in Participation.objects.filter(
        joueur_id=joueur_id,
        seance__statut=StatutSeance.VALIDEE,
        seance__date__lte=date_calcul,
    ).values_list("seance__date", "seance__duree_min", "rpe_cardio", "rpe_musculaire", "rpe_teta"):
        cardio, musculaire, teta = rpe
        if cardio is None or musculaire is None or teta is None:
            # Le déclencheur de complétude l'interdit pour une séance validée (ADR-0008).
            raise ValueError(f"participation incomplète dans une séance validée du {jour}")
        participations.append(ParticipationValidee(jour, duree, cardio, musculaire, teta))
    return calendrier(participations, parametres, date_calcul)


def calculer_charges_glissantes(
    joueur_id: int, date_calcul: datetime.date, parametres: Parametres
) -> list[ChargesGlissantes]:
    """CE courte et CE longue d'un joueur pour chaque jour de son calendrier."""
    return charges_glissantes(calculer_joueur(joueur_id, date_calcul, parametres), parametres)
