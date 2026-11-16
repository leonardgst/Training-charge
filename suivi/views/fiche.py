"""Fiche d'un joueur (US-11, F12) : charge et sensations, sans formule dans la vue ni le gabarit.

Le joueur est lu par `joueurs_suivis` avant tout appel à l'adaptateur : un joueur d'une autre
catégorie ou un invité répond 404. Les valeurs viennent du moteur (`suivi/calculs.py`).
"""

from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_safe

from engine.modeles import Etat
from suivi.acces import joueurs_suivis, participations_visibles
from suivi.calculs import (
    calculer_charges_glissantes,
    calculer_detail_sensations,
    calculer_intensite,
    charges_de_seance,
    parametres,
)
from suivi.graphiques import (
    specification_barres_sensations,
    specification_charges,
    specification_heatmap,
)
from suivi.horloge import aujourd_hui
from suivi.middleware import RequeteStaff
from suivi.models import StatutSeance

SEANCES_AFFICHEES = 10
JOURS_AFFICHES = 28

LIBELLES_ETAT = {
    Etat.OK: "",
    Etat.HISTORIQUE_INSUFFISANT: "Historique insuffisant",
    Etat.NON_CALCULABLE: "Non calculable",
    Etat.REPONSES_INSUFFISANTES: "Réponses insuffisantes",
}


@require_safe
def fiche_joueur(request: RequeteStaff, pk: int) -> HttpResponse:
    """RPE, barres de CE, sensations de la dernière entrée et heatmap sur 7 jours."""
    joueur = joueurs_suivis(request.preparateur).filter(pk=pk).first()
    if joueur is None:
        raise Http404
    jour = aujourd_hui()
    params = parametres()
    participations = list(
        participations_visibles(request.preparateur)
        .filter(joueur=joueur, seance__statut=StatutSeance.VALIDEE, seance__date__lte=jour)
        .select_related("seance")
        .order_by("-seance__date", "-seance__pk")[:SEANCES_AFFICHEES]
    )
    # Le lien vers la séance n'existe que pour une séance organisée par sa propre catégorie :
    # le détail d'une autre séance répond 404 (joueur invité ailleurs).
    lignes = [
        (
            p,
            charges_de_seance(p.seance, [p], params)[p.pk],
            p.seance.categorie_organisatrice_id == request.preparateur.categorie_id,
        )
        for p in participations
    ]
    charges = calculer_charges_glissantes(joueur.pk, jour, params)[-JOURS_AFFICHES:]
    intensites = {z.jour: z for z in calculer_intensite(joueur.pk, jour, params)}
    valeurs = [
        (c, intensites[c.jour], LIBELLES_ETAT[intensites[c.jour].etat]) for c in reversed(charges)
    ]
    sensations = calculer_detail_sensations(joueur.pk, jour, params)
    # Mise en tableau seulement : une ligne par indicateur, une cellule par jour.
    lignes_sensations = [
        (libelle, [c for j in sensations.jours for c in j.cellules if c.code == code])
        for code, libelle in sensations.libelles.items()
    ]
    lignes_derniere = (
        [(sensations.libelles[c.code], c) for c in sensations.derniere.cellules]
        if sensations.derniere
        else []
    )
    return render(
        request,
        "suivi/fiche_joueur.html",
        {
            "rubrique": "joueurs",
            "joueur": joueur,
            "jour": jour,
            "lignes": lignes,
            "valeurs": valeurs,
            "specification": specification_charges(charges),
            "derniere": sensations.derniere,
            "lignes_derniere": lignes_derniere,
            "entree_sur_7_jours": any(j.a_entree for j in sensations.jours),
            "etat_insuffisant": Etat.REPONSES_INSUFFISANTES,
            "libelle_insuffisant": LIBELLES_ETAT[Etat.REPONSES_INSUFFISANTES],
            "jours_sensations": sensations.jours,
            "lignes_sensations": lignes_sensations,
            "specification_barres": specification_barres_sensations(
                sensations.derniere, sensations.libelles
            ),
            "specification_heatmap": specification_heatmap(sensations.jours, sensations.libelles),
        },
    )
