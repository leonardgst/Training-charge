"""Vue « Forme actuelle » (US-10, ADR-0018) : les valeurs viennent du moteur, sans formule."""

import datetime

from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_safe

from engine.modeles import EtatForme, FormeActuelle
from suivi.acces import joueurs_suivis
from suivi.calculs import calculer_forme_actuelle, parametres
from suivi.graphiques import specification_forme
from suivi.horloge import aujourd_hui
from suivi.middleware import RequeteStaff

LIBELLES_ETAT = {
    EtatForme.OK: "Point affiché",
    EtatForme.ABSENT: "Absent",
    EtatForme.HISTORIQUE_INSUFFISANT: "Historique insuffisant",
    EtatForme.NON_CALCULABLE: "Non calculable",
    EtatForme.PAS_D_ENTREE_RECENTE: "Pas d'entrée récente",
    EtatForme.REPONSES_INSUFFISANTES: "Réponses insuffisantes",
}


def _etat(forme: FormeActuelle) -> str:
    if forme.etat is EtatForme.ABSENT:
        return f"Absent depuis {forme.absent_depuis_jours} jours"
    return LIBELLES_ETAT[forme.etat]


@require_safe
def forme_actuelle(request: RequeteStaff) -> HttpResponse:
    """Nuage « Forme actuelle » du jour, tableau de ses valeurs, joueurs sans point."""
    jour: datetime.date = aujourd_hui()
    params = parametres()
    formes = [
        (f"{j.prenom} {j.nom}", calculer_forme_actuelle(j.pk, jour, params))
        for j in joueurs_suivis(request.preparateur).filter(actif=True).order_by("nom", "prenom")
    ]
    return render(
        request,
        "suivi/forme_actuelle.html",
        {
            "rubrique": "forme",
            "jour": jour,
            "specification": specification_forme(formes, params),
            "avec_point": [(nom, forme) for nom, forme in formes if forme.point is not None],
            "sans_point": [(nom, _etat(forme)) for nom, forme in formes if forme.point is None],
        },
    )
