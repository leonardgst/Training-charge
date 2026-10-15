"""Vues du staff : toute requête passe par `suivi/acces.py` (ADR-0005).

Le préparateur connecté est posé sur `request.preparateur` par
`ProfilPreparateurRequisMiddleware`, avant toute vue de ce module.
"""

from django.contrib import messages
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods, require_POST, require_safe

from suivi.acces import joueurs_suivis
from suivi.forms import JoueurForm
from suivi.middleware import RequeteStaff
from suivi.models import Joueur


def _joueur_suivi(request: RequeteStaff, pk: int) -> Joueur:
    """Joueur de la catégorie du préparateur ; 404 pour tout autre, qu'il existe ou non."""
    joueur = joueurs_suivis(request.preparateur).filter(pk=pk).first()
    if joueur is None:
        raise Http404
    return joueur


@require_safe
def joueurs(request: RequeteStaff) -> HttpResponse:
    """Joueurs de sa catégorie : actifs, puis archivés (US-15)."""
    tous = list(joueurs_suivis(request.preparateur).order_by("nom", "prenom", "pk"))
    return render(
        request,
        "suivi/joueurs.html",
        {
            "rubrique": "joueurs",
            "actifs": [joueur for joueur in tous if joueur.actif],
            "archives": [joueur for joueur in tous if not joueur.actif],
        },
    )


def _formulaire(request: RequeteStaff, joueur: Joueur, message: str) -> HttpResponse:
    form = JoueurForm(request.POST if request.method == "POST" else None, instance=joueur)
    if form.is_valid():
        joueur = form.save(commit=False)
        joueur.updated_by = request.user
        joueur.save()
        messages.success(request, message.format(joueur=joueur))
        return redirect("joueurs")
    return render(
        request,
        "suivi/joueur_formulaire.html",
        {"rubrique": "joueurs", "form": form, "joueur": joueur},
    )


@require_http_methods(["GET", "HEAD", "POST"])
def joueur_creer(request: RequeteStaff) -> HttpResponse:
    joueur = Joueur(categorie_reference=request.preparateur.categorie)
    return _formulaire(request, joueur, "{joueur} est ajouté à la catégorie.")


@require_http_methods(["GET", "HEAD", "POST"])
def joueur_modifier(request: RequeteStaff, pk: int) -> HttpResponse:
    return _formulaire(request, _joueur_suivi(request, pk), "{joueur} est modifié.")


def _changer_activite(request: RequeteStaff, pk: int, actif: bool, message: str) -> HttpResponse:
    joueur = _joueur_suivi(request, pk)
    joueur.actif = actif
    joueur.updated_by = request.user
    joueur.save()
    messages.success(request, message.format(joueur=joueur))
    return redirect("joueurs")


@require_POST
def joueur_archiver(request: RequeteStaff, pk: int) -> HttpResponse:
    """Départ du groupe : réversible, données conservées (ADR-0009)."""
    return _changer_activite(
        request, pk, False, "{joueur} est archivé : il n’apparaît plus dans les listes de saisie."
    )


@require_POST
def joueur_reactiver(request: RequeteStaff, pk: int) -> HttpResponse:
    return _changer_activite(request, pk, True, "{joueur} est réactivé.")
