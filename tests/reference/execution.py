"""Exécution d'un cas : chargement en base et appels du moteur.

`charger_en_base` fait partie du harnais et est testé dès la PR 3.1. Les deux fonctions
`executer_*` sont les deux points de branchement sur le code testé ; elles seront écrites
avec le moteur (PR 3.2) et en attendant refusent de s'exécuter.
"""

import datetime
from collections.abc import Mapping

from tests.reference.harnais import CasReference, Cle, Resultat

DATE_DE_NAISSANCE = datetime.date(2007, 1, 1)
FUSEAU = datetime.UTC


def charger_en_base(cas: CasReference) -> dict[str, int]:
    """Écrit le cas dans la base courante par l'ORM ; renvoie l'identifiant de chaque joueur.

    Les séances sont créées en brouillon puis validées une fois leurs participations
    posées, comme le fait la saisie : le déclencheur de complétude s'applique donc.
    """
    from suivi.models import (
        Categorie,
        EntreeSensations,
        Indicateur,
        Joueur,
        Participation,
        Reponse,
        Seance,
    )

    codes = (
        set(cas.joueurs.values())
        | {s.categorie for s in cas.seances}
        | {i.categorie for i in cas.indicateurs}
    )
    categories = {code: Categorie.objects.create(code=code, libelle=code) for code in sorted(codes)}
    joueurs = {
        nom: Joueur.objects.create(
            nom=nom,
            prenom="Reference",
            date_naissance=DATE_DE_NAISSANCE,
            categorie_reference=categories[categorie],
        )
        for nom, categorie in cas.joueurs.items()
    }
    indicateurs = {
        (i.categorie, i.code): Indicateur.objects.create(
            categorie=categories[i.categorie],
            code=i.code,
            libelle=i.code,
            type=i.type,
            borne_min=i.borne_min,
            borne_max=i.borne_max,
            sens=i.sens,
            poids=i.poids,
            inclus_score=i.inclus_score,
        )
        for i in cas.indicateurs
    }
    for ref in cas.seances:
        seance = Seance.objects.create(
            categorie_organisatrice=categories[ref.categorie],
            date=ref.date,
            type=ref.type,
            duree_min=ref.duree_min,
        )
        Participation.objects.bulk_create(
            Participation(
                seance=seance,
                joueur=joueurs[p.joueur],
                rpe_cardio=p.rpe_cardio,
                rpe_musculaire=p.rpe_musculaire,
                rpe_teta=p.rpe_teta,
            )
            for p in cas.participations
            if p.seance_id == ref.id
        )
        if ref.statut == "validee":
            valide_le = datetime.datetime.combine(ref.date, datetime.time(20, 0), tzinfo=FUSEAU)
            Seance.objects.filter(pk=seance.pk).update(statut="validee", validated_at=valide_le)
    entrees: dict[tuple[str, datetime.date], EntreeSensations] = {}
    for r in cas.reponses:
        cle = (r.joueur, r.date)
        if cle not in entrees:
            entrees[cle] = EntreeSensations.objects.create(joueur=joueurs[r.joueur], date=r.date)
        Reponse.objects.create(
            entree=entrees[cle],
            indicateur=indicateurs[(cas.joueurs[r.joueur], r.indicateur)],
            valeur=r.valeur,
        )
    return {nom: joueur.pk for nom, joueur in joueurs.items()}


def executer_sans_base(cas: CasReference, date_calcul: datetime.date) -> Mapping[Cle, Resultat]:
    """Appelle directement le moteur sur les données du cas, sans base (retour rapide)."""
    raise NotImplementedError("engine/ n'existe pas encore")


def executer_sur_base(
    cas: CasReference, joueurs: Mapping[str, int], date_calcul: datetime.date
) -> Mapping[Cle, Resultat]:
    """Appelle l'adaptateur puis le moteur sur la base chargée ; cette version fait foi."""
    raise NotImplementedError("suivi/calculs.py n'existe pas encore")
