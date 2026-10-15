"""Exécution d'un cas : chargement en base et appels du moteur.

`charger_en_base` fait partie du harnais. Les deux fonctions `executer_*` sont les deux
points de branchement sur le code testé : elles étendent leurs résultats à chaque PR de la
phase 3 (ici, jusqu'au score et au z-score de sensations).
"""

import dataclasses
import datetime
from collections.abc import Mapping, Sequence

from engine.charge import calendrier, charges_glissantes
from engine.modeles import (
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


def _resultats(
    nom: str, jours: Sequence[JourCalcule], parametres: Parametres, date_calcul: datetime.date
) -> dict[Cle, Resultat]:
    obtenu: dict[Cle, Resultat] = {}
    for jour in jours:
        if jour.jour <= date_calcul:
            obtenu[(nom, jour.jour, "charge_jour")] = Resultat(jour.charge_jour, "ok")
    glissantes = charges_glissantes(jours, parametres)
    for glissante in glissantes:
        if glissante.jour <= date_calcul:
            obtenu[(nom, glissante.jour, "ce_courte")] = Resultat(glissante.ce_courte, "ok")
            obtenu[(nom, glissante.jour, "ce_longue")] = Resultat(glissante.ce_longue, "ok")
    for z in intensite(glissantes, parametres):
        if z.jour <= date_calcul:
            obtenu[(nom, z.jour, "intensite")] = Resultat(z.valeur, z.etat.value)
    return obtenu


def _resultats_sensations(
    nom: str, scores_entrees: Sequence[ScoreEntree], z: Sequence[ZScore], date_calcul: datetime.date
) -> dict[Cle, Resultat]:
    obtenu: dict[Cle, Resultat] = {}
    for score in scores_entrees:
        if score.jour <= date_calcul:
            obtenu[(nom, score.jour, "score_sensations")] = Resultat(score.valeur, score.etat.value)
    for zscore in z:
        if zscore.jour <= date_calcul:
            obtenu[(nom, zscore.jour, "sensations_z")] = Resultat(zscore.valeur, zscore.etat.value)
    return obtenu


def _sensations_sans_base(
    cas: CasReference, nom: str, parametres: Parametres, date_calcul: datetime.date
) -> dict[Cle, Resultat]:
    """Sensations d'un joueur calculées depuis les CSV du cas, comme le fait l'adaptateur."""
    categorie = cas.joueurs[nom]
    indicateurs = [
        IndicateurScore(
            code=i.code,
            borne_min=i.borne_min,
            borne_max=i.borne_max,
            haut_est_bon=i.sens == "haut_bon",
            poids=float(i.poids),
        )
        for i in cas.indicateurs
        if i.categorie == categorie and i.inclus_score and i.type == "note"
    ]
    codes = {i.code for i in indicateurs}
    par_date: dict[datetime.date, dict[str, int]] = {}
    for r in cas.reponses:
        if r.joueur == nom and r.date <= date_calcul:
            reponses = par_date.setdefault(r.date, {})
            if r.indicateur in codes:
                reponses[r.indicateur] = r.valeur
    entrees = [EntreeSensations(jour, reponses) for jour, reponses in par_date.items()]
    resultats = scores(entrees, indicateurs, parametres)
    return _resultats_sensations(nom, resultats, sensations_z(resultats, parametres), date_calcul)


def parametres_du_cas(cas: CasReference) -> Parametres:
    """Paramètres de `config/calcul.toml`, surchargés par le `[parametres]` du cas."""
    from suivi.calculs import lire_parametres

    return dataclasses.replace(lire_parametres(), **cas.parametres)  # type: ignore[arg-type]


def executer_sans_base(cas: CasReference, date_calcul: datetime.date) -> Mapping[Cle, Resultat]:
    """Appelle directement le moteur sur les données du cas, sans base (retour rapide).

    Réservé aux cas sans brouillon : écarter les brouillons est le rôle de l'adaptateur,
    et les cas qui le vérifient (C5, C9, C10, C15) ne tournent que sur la base.
    """
    if any(seance.statut != "validee" for seance in cas.seances):
        raise ValueError(f"{cas.nom} : un brouillon ne se teste que sur la base")
    parametres = parametres_du_cas(cas)
    dates = {seance.id: seance for seance in cas.seances}
    obtenu: dict[Cle, Resultat] = {}
    for nom in cas.joueurs:
        participations = []
        for p in cas.participations:
            if p.joueur != nom:
                continue
            seance = dates[p.seance_id]
            if p.rpe_cardio is None or p.rpe_musculaire is None or p.rpe_teta is None:
                raise ValueError(f"{cas.nom} : RPE manquant dans une séance validée")
            participations.append(
                ParticipationValidee(
                    seance.date, seance.duree_min, p.rpe_cardio, p.rpe_musculaire, p.rpe_teta
                )
            )
        jours = calendrier(participations, parametres, date_calcul)
        obtenu.update(_resultats(nom, jours, parametres, date_calcul))
        obtenu.update(_sensations_sans_base(cas, nom, parametres, date_calcul))
    return obtenu


def executer_sur_base(
    cas: CasReference, joueurs: Mapping[str, int], date_calcul: datetime.date
) -> Mapping[Cle, Resultat]:
    """Appelle l'adaptateur puis le moteur sur la base chargée ; cette version fait foi."""
    from suivi.calculs import calculer_joueur

    parametres = parametres_du_cas(cas)
    obtenu: dict[Cle, Resultat] = {}
    for nom, joueur_id in joueurs.items():
        jours = calculer_joueur(joueur_id, date_calcul, parametres)
        obtenu.update(_resultats(nom, jours, parametres, date_calcul))
        obtenu.update(_sensations_sans_base(cas, nom, parametres, date_calcul))
    return obtenu
