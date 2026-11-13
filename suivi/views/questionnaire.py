"""Questionnaire du jour par le lien du joueur (US-08, US-09, ADR-0006, ADR-0008).

Seule vue qui accepte le jeton. Elle est hors de la connexion obligatoire : une redirection
vers la connexion placerait le jeton dans l'adresse. Le joueur n'a ni compte ni session ; le
jeton désigne un joueur, et la vue n'atteint que ses indicateurs et son entrée du jour (A4).
Un jeton invalide, révoqué, régénéré ou d'un joueur archivé donne le même 404 (A5).
"""

from django.contrib.auth.decorators import login_not_required
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_variables
from django.views.decorators.http import require_http_methods

from suivi.forms import QuestionnaireForm
from suivi.horloge import aujourd_hui
from suivi.liens import empreinte, joueur_du_lien
from suivi.questionnaire import (
    LienPerime,
    enregistrer_entree,
    indicateurs_du_questionnaire,
    reponses_du_jour,
)


@login_not_required
@never_cache
@require_http_methods(["GET", "POST"])
@sensitive_variables("jeton")
def questionnaire(request: HttpRequest, jeton: str) -> HttpResponse:
    joueur = joueur_du_lien(jeton)
    if joueur is None:
        raise Http404
    jour = aujourd_hui()
    indicateurs = indicateurs_du_questionnaire(joueur)
    reponses = reponses_du_jour(joueur, jour)
    enregistre = nouvelle_journee = False

    if request.method == "POST":
        formulaire = QuestionnaireForm(indicateurs, request.POST, reponses=reponses)
        if request.POST.get("date") != jour.isoformat():
            # Page chargée un autre jour : rien n'est rangé dans le jour courant avant relecture.
            nouvelle_journee = True
            formulaire = QuestionnaireForm(indicateurs, reponses=reponses, initial={"date": jour})
        elif indicateurs and formulaire.is_valid():
            try:
                enregistrer_entree(joueur, jour, formulaire.valeurs(), empreinte(jeton))
            except LienPerime:
                raise Http404 from None
            enregistre = True
    else:
        formulaire = QuestionnaireForm(indicateurs, reponses=reponses, initial={"date": jour})

    return render(
        request,
        "suivi/questionnaire.html",
        {
            "joueur": joueur,
            "formulaire": formulaire,
            "jour": jour,
            "enregistre": enregistre,
            "nouvelle_journee": nouvelle_journee,
        },
    )
