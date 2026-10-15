"""Vues du staff : toute requête passe par `suivi/acces.py` (ADR-0005).

Le préparateur connecté est posé sur `request.preparateur` par
`ProfilPreparateurRequisMiddleware`, avant toute vue de ce module.
"""

from urllib.parse import urlencode

from django.contrib import messages
from django.db import transaction
from django.db.models import Q, QuerySet
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST, require_safe

from suivi.acces import annuaire, joueurs_suivis, participations_visibles, seances_organisees
from suivi.forms import JoueurForm, SeanceForm
from suivi.horloge import aujourd_hui
from suivi.middleware import RequeteStaff
from suivi.models import Joueur, Seance, StatutSeance, TypeSeance

# Nombre maximal de joueurs affichés par une recherche dans l'annuaire.
RESULTATS_ANNUAIRE = 20


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


# --- Séances ---------------------------------------------------------------------------


def _seance_organisee(request: RequeteStaff, pk: int) -> Seance:
    """Séance de la catégorie du préparateur ; 404 pour toute autre, qu'elle existe ou non."""
    seance = seances_organisees(request.preparateur).filter(pk=pk).first()
    if seance is None:
        raise Http404
    return seance


def _joueurs_actifs(request: RequeteStaff) -> QuerySet[Joueur]:
    return joueurs_suivis(request.preparateur).filter(actif=True).order_by("nom", "prenom", "pk")


@require_http_methods(["GET", "HEAD", "POST"])
def seance_creer(request: RequeteStaff) -> HttpResponse:
    """En-tête et participants, pré-remplis avec les joueurs actifs de sa catégorie (US-03)."""
    joueurs = _joueurs_actifs(request)
    seance = Seance(categorie_organisatrice=request.preparateur.categorie)
    if request.method == "POST":
        form = SeanceForm(request.POST, instance=seance, joueurs=joueurs)
        if form.is_valid():
            with transaction.atomic():
                seance = form.save(commit=False)
                seance.created_by = seance.updated_by = request.user
                seance.save()
                for joueur in form.cleaned_data["participants"]:
                    seance.participations.create(joueur=joueur, updated_by=request.user)
            messages.success(request, "La séance est créée en brouillon.")
            return redirect("seance", pk=seance.pk)
    else:
        form = SeanceForm(
            instance=seance,
            joueurs=joueurs,
            initial={
                "date": aujourd_hui(),
                "type": TypeSeance.FOOT,
                "participants": [joueur.pk for joueur in joueurs],
            },
        )
    return render(request, "suivi/seance_creer.html", {"rubrique": "nouvelle_seance", "form": form})


@require_safe
def seance_detail(request: RequeteStaff, pk: int) -> HttpResponse:
    """Une séance, ses participants et, en brouillon, la recherche dans l'annuaire."""
    seance = _seance_organisee(request, pk)
    participations = (
        participations_visibles(request.preparateur)
        .filter(seance=seance)
        .select_related("joueur__categorie_reference")
        .order_by("joueur__nom", "joueur__prenom", "pk")
    )
    recherche = request.GET.get("q", "").strip()
    resultats = []
    if recherche and seance.statut == StatutSeance.BROUILLON:
        resultats = list(
            annuaire(request.preparateur)
            .filter(Q(nom__icontains=recherche) | Q(prenom__icontains=recherche))
            .exclude(pk__in=[participation.joueur_id for participation in participations])[
                :RESULTATS_ANNUAIRE
            ]
        )
    return render(
        request,
        "suivi/seance.html",
        {
            "seance": seance,
            "brouillon": seance.statut == StatutSeance.BROUILLON,
            "participations": participations,
            "recherche": recherche,
            "resultats": resultats,
            "limite": RESULTATS_ANNUAIRE,
        },
    )


def _seance_en_brouillon(request: RequeteStaff, pk: int) -> Seance | None:
    """Les participants ne se changent ici que sur un brouillon ; sinon, un message."""
    seance = _seance_organisee(request, pk)
    if seance.statut != StatutSeance.BROUILLON:
        messages.error(request, "Cette séance est validée : ses participants ne changent plus ici.")
        return None
    return seance


def _retour_a_la_seance(pk: int, recherche: str = "") -> HttpResponse:
    url = reverse("seance", kwargs={"pk": pk})
    return redirect(url + ("?" + urlencode({"q": recherche}) if recherche else ""))


def _toucher(seance: Seance, request: RequeteStaff) -> None:
    """Changer les participants modifie la séance : date et auteur enregistrés (ADR-0008)."""
    seance.updated_by = request.user
    seance.save(update_fields=["updated_by", "updated_at"])


@require_POST
def participant_ajouter(request: RequeteStaff, pk: int) -> HttpResponse:
    """Ajoute un joueur de l'annuaire : un absent revenu, ou un joueur invité (R24)."""
    seance = _seance_en_brouillon(request, pk)
    recherche = request.POST.get("q", "").strip()
    if seance is None:
        return _retour_a_la_seance(pk)
    saisi = request.POST.get("joueur", "")
    # L'annuaire ne contient que des joueurs actifs : un archivé est introuvable ici.
    ligne = annuaire(request.preparateur).filter(pk=int(saisi)).first() if saisi.isdigit() else None
    if ligne is None:
        raise Http404
    nom = f"{ligne['prenom']} {ligne['nom']}"
    deja = participations_visibles(request.preparateur).filter(seance=seance, joueur_id=ligne["pk"])
    if deja.exists():
        messages.info(request, f"{nom} participe déjà à la séance.")
    else:
        with transaction.atomic():
            seance.participations.create(joueur_id=ligne["pk"], updated_by=request.user)
            _toucher(seance, request)
        messages.success(request, f"{nom} est ajouté à la séance.")
    return _retour_a_la_seance(pk, recherche)


@require_POST
def participant_retirer(request: RequeteStaff, pk: int, participation_pk: int) -> HttpResponse:
    """Retire un absent ; ses éventuels RPE disparaissent avec sa participation."""
    seance = _seance_en_brouillon(request, pk)
    if seance is None:
        return _retour_a_la_seance(pk)
    participation = (
        participations_visibles(request.preparateur)
        .filter(pk=participation_pk, seance=seance)
        .select_related("joueur")
        .first()
    )
    if participation is None:
        raise Http404
    with transaction.atomic():
        participation.delete()
        _toucher(seance, request)
    messages.success(request, f"{participation.joueur} est retiré de la séance.")
    return _retour_a_la_seance(pk)
