"""Adaptateur entre la base et le moteur de calcul.

Seul code qui lit la base pour le moteur. Il ne charge que les participations des séances
validées (les brouillons n'entrent dans aucun calcul) et les données datées au plus tard
de la date de calcul (C9).
"""

import datetime
import tomllib
from collections.abc import Iterable
from functools import cache
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

from engine.charge import calendrier, charge_seance, charges_glissantes
from engine.modeles import (
    ChargesGlissantes,
    EntreeSensations,
    IndicateurScore,
    JourCalcule,
    Parametres,
    ParticipationValidee,
    ScoreEntree,
    ZScore,
)
from engine.sensations import scores, sensations_z
from engine.zscore import intensite
from suivi.models import EntreeSensations as EntreeEnBase
from suivi.models import (
    Indicateur,
    Joueur,
    Participation,
    Reponse,
    Seance,
    SensIndicateur,
    StatutSeance,
    TypeIndicateur,
)

CHEMIN_PARAMETRES = Path(__file__).resolve().parent.parent / "config" / "calcul.toml"


def lire_parametres(chemin: Path = CHEMIN_PARAMETRES) -> Parametres:
    """Lit et valide `config/calcul.toml` ; toute anomalie interrompt le démarrage."""
    with chemin.open("rb") as fichier:
        brut = tomllib.load(fichier)
    entiers = (
        "fenetre_courte_jours",
        "fenetre_longue_jours",
        "reference_jours",
        "reference_min_jours",
        "sensations_reference_jours",
        "sensations_reference_min_entrees",
    )
    positifs = ("facteur_echelle_charge", "tolerance_ecart_type_nul", "score_poids_min")
    attendues = {*positifs, *entiers}
    if set(brut) != attendues:
        raise ImproperlyConfigured(f"{chemin.name} : clés attendues {sorted(attendues)}")
    for cle in positifs:
        valeur = brut[cle]
        if isinstance(valeur, bool) or not isinstance(valeur, int | float) or valeur <= 0:
            raise ImproperlyConfigured(f"{chemin.name} : {cle} doit être positif")
    for cle in entiers:
        if isinstance(brut[cle], bool) or not isinstance(brut[cle], int) or brut[cle] < 1:
            raise ImproperlyConfigured(f"{chemin.name} : {cle} doit être un entier d'au moins 1")
    if brut["fenetre_courte_jours"] >= brut["fenetre_longue_jours"]:
        raise ImproperlyConfigured(
            f"{chemin.name} : fenetre_courte_jours doit être inférieure à fenetre_longue_jours"
        )
    if not 2 <= brut["reference_min_jours"] <= brut["reference_jours"]:
        raise ImproperlyConfigured(
            f"{chemin.name} : reference_min_jours doit être compris entre 2 et reference_jours"
        )
    if not 2 <= brut["sensations_reference_min_entrees"] <= brut["sensations_reference_jours"]:
        raise ImproperlyConfigured(
            f"{chemin.name} : sensations_reference_min_entrees doit être compris entre 2 et "
            "sensations_reference_jours"
        )
    if brut["score_poids_min"] > 1:
        raise ImproperlyConfigured(f"{chemin.name} : score_poids_min doit être au plus 1")
    return Parametres(
        facteur_echelle_charge=float(brut["facteur_echelle_charge"]),
        fenetre_courte_jours=brut["fenetre_courte_jours"],
        fenetre_longue_jours=brut["fenetre_longue_jours"],
        reference_jours=brut["reference_jours"],
        reference_min_jours=brut["reference_min_jours"],
        tolerance_ecart_type_nul=float(brut["tolerance_ecart_type_nul"]),
        score_poids_min=float(brut["score_poids_min"]),
        sensations_reference_jours=brut["sensations_reference_jours"],
        sensations_reference_min_entrees=brut["sensations_reference_min_entrees"],
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


def charges_de_seance(
    seance: Seance, participations: Iterable[Participation], parametres: Parametres
) -> dict[int, float]:
    """Charge de séance de chaque participation, par identifiant de participation.

    Les participations viennent de l'appelant, lues dans son périmètre (`suivi/acces.py`) ;
    elles doivent toutes appartenir à `seance`. Une séance en brouillon n'entre dans aucun
    calcul (C5) : rien n'est calculé.
    """
    if seance.statut != StatutSeance.VALIDEE:
        return {}
    charges = {}
    for participation in participations:
        if participation.seance_id != seance.pk:
            raise ValueError(f"la participation {participation.pk} n'appartient pas à la séance")
        cardio, musculaire, teta = (
            participation.rpe_cardio,
            participation.rpe_musculaire,
            participation.rpe_teta,
        )
        if cardio is None or musculaire is None or teta is None:
            # Le déclencheur de complétude l'interdit pour une séance validée (ADR-0008).
            raise ValueError(f"participation incomplète dans une séance validée du {seance.date}")
        entree = ParticipationValidee(seance.date, seance.duree_min, cardio, musculaire, teta)
        charges[participation.pk] = charge_seance(entree, parametres)
    return charges


def calculer_charges_glissantes(
    joueur_id: int, date_calcul: datetime.date, parametres: Parametres
) -> list[ChargesGlissantes]:
    """CE courte et CE longue d'un joueur pour chaque jour de son calendrier."""
    return charges_glissantes(calculer_joueur(joueur_id, date_calcul, parametres), parametres)


def calculer_intensite(
    joueur_id: int, date_calcul: datetime.date, parametres: Parametres
) -> list[ZScore]:
    """Z-score d'intensité d'un joueur pour chaque jour de son calendrier."""
    return intensite(calculer_charges_glissantes(joueur_id, date_calcul, parametres), parametres)


def calculer_sensations(
    joueur_id: int, date_calcul: datetime.date, parametres: Parametres
) -> tuple[list[ScoreEntree], list[ZScore]]:
    """Score et z-score de chaque entrée de sensations d'un joueur, jusqu'à `date_calcul`.

    La configuration est celle d'aujourd'hui, pour tout le passé (ADR-0016) : les
    indicateurs actifs, notés et inclus dans le score de la catégorie de référence du joueur.
    """
    categorie_id = Joueur.objects.values_list("categorie_reference_id", flat=True).get(pk=joueur_id)
    indicateurs = {
        i.pk: IndicateurScore(
            code=i.code,
            borne_min=i.borne_min,
            borne_max=i.borne_max,
            haut_est_bon=i.sens == SensIndicateur.HAUT_BON,
            poids=float(i.poids),
        )
        for i in Indicateur.objects.filter(
            categorie_id=categorie_id,
            actif=True,
            inclus_score=True,
            type=TypeIndicateur.NOTE,
        )
    }
    par_date: dict[datetime.date, dict[str, int]] = {
        jour: {}
        for jour in EntreeEnBase.objects.filter(joueur_id=joueur_id, date__lte=date_calcul)
        .order_by("date")
        .values_list("date", flat=True)
    }
    for jour, indicateur_id, valeur in Reponse.objects.filter(
        entree__joueur_id=joueur_id, entree__date__lte=date_calcul
    ).values_list("entree__date", "indicateur_id", "valeur"):
        if indicateur_id in indicateurs:
            par_date[jour][indicateurs[indicateur_id].code] = valeur
    entrees = [EntreeSensations(jour, reponses) for jour, reponses in par_date.items()]
    resultats = scores(entrees, list(indicateurs.values()), parametres)
    return resultats, sensations_z(resultats, parametres)
