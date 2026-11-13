"""Vues du staff : toute requête passe par `suivi/acces.py` (ADR-0005).

Le préparateur connecté est posé sur `request.preparateur` par
`ProfilPreparateurRequisMiddleware`, avant toute vue de ce module.
"""

from urllib.parse import urlencode

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q, QuerySet
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_variables
from django.views.decorators.http import require_http_methods, require_POST, require_safe

from suivi.acces import (
    annuaire,
    entrees_visibles,
    joueurs_ayant_repondu,
    joueurs_suivis,
    liens_actifs,
    participations_visibles,
    seances_organisees,
)
from suivi.badge import etat_questionnaire
from suivi.calculs import charges_de_seance, parametres
from suivi.forms import (
    COLONNES_RPE,
    GrilleRpeForm,
    JoueurForm,
    QuestionnaireForm,
    RpeParticipantForm,
    SeanceEnteteForm,
    SeanceForm,
)
from suivi.horloge import aujourd_hui
from suivi.liens import JoueurArchive, archiver_joueur, creer_lien, qr_data_uri, revoquer_liens
from suivi.middleware import RequeteStaff
from suivi.models import EntreeSensations, Joueur, Participation, Seance, StatutSeance, TypeSeance
from suivi.questionnaire import (
    EntreeSupprimee,
    corriger_entree,
    indicateurs_du_questionnaire,
    supprimer_entree,
)

# Nombre maximal de joueurs affichés par une recherche dans l'annuaire.
RESULTATS_ANNUAIRE = 20
# Séances par page de l'historique.
SEANCES_PAR_PAGE = 30


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
            "avec_lien": {lien.joueur_id for lien in liens_actifs(request.preparateur)},
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
    if actif:
        joueur.actif = True
        joueur.updated_by = request.user
        joueur.save()
    else:
        # Départ du groupe : le lien ne doit plus ouvrir le questionnaire (ADR-0006, ADR-0009).
        archiver_joueur(joueur, request.user)
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


# --- Liens joueurs ---------------------------------------------------------------------


@require_POST
@never_cache
@sensitive_variables("jeton", "adresse")
def lien_generer(request: RequeteStaff, pk: int) -> HttpResponse:
    """Crée le lien du joueur (le précédent est révoqué) et l'affiche une seule fois (US-07).

    Le jeton est dans la réponse seulement : ni session, ni message, ni redirection, ni
    journal. Actualiser la page renvoie le formulaire et crée un autre lien.
    """
    joueur = _joueur_suivi(request, pk)
    if not joueur.actif:
        messages.error(request, f"{joueur} est archivé : réactive-le avant de créer son lien.")
        return redirect("joueurs")
    try:
        jeton = creer_lien(joueur, request.user)
    except JoueurArchive:
        messages.error(request, f"{joueur} est archivé : réactive-le avant de créer son lien.")
        return redirect("joueurs")
    adresse = request.build_absolute_uri(reverse("questionnaire", kwargs={"jeton": jeton}))
    return render(
        request,
        "suivi/lien_joueur.html",
        {
            "rubrique": "joueurs",
            "joueur": joueur,
            "adresse": adresse,
            "qr_code": qr_data_uri(adresse),
        },
    )


@require_POST
def lien_revoquer(request: RequeteStaff, pk: int) -> HttpResponse:
    joueur = _joueur_suivi(request, pk)
    if revoquer_liens(joueur):
        messages.success(request, f"Le lien de {joueur} est révoqué : il n’ouvre plus rien.")
    else:
        messages.info(request, f"{joueur} n’a pas de lien actif.")
    return redirect("joueurs")


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
def seances(request: RequeteStaff) -> HttpResponse:
    """Historique des séances de sa catégorie, des plus récentes aux plus anciennes (US-06)."""
    toutes = (
        seances_organisees(request.preparateur)
        .annotate(nombre_participants=Count("participations"))
        .order_by("-date", "-pk")
    )
    page = Paginator(toutes, SEANCES_PAR_PAGE).get_page(request.GET.get("page"))
    return render(request, "suivi/seances.html", {"rubrique": "seances", "page": page})


def _participations(request: RequeteStaff, seance: Seance) -> list[Participation]:
    """Participations de la séance, chacune avec son badge de questionnaire (F10).

    Seuls les joueurs suivis ont un badge : l'entrée d'un joueur invité n'est pas lisible
    (ADR-0005), il reste donc sans état, comme un jour sans questionnaire.
    """
    participations = list(
        participations_visibles(request.preparateur)
        .filter(seance=seance)
        .select_related("joueur__categorie_reference")
        .order_by("joueur__nom", "joueur__prenom", "pk")
    )
    ont_repondu = set(joueurs_ayant_repondu(request.preparateur, seance.date))
    aujourdhui = aujourd_hui()
    for participation in participations:
        joueur = participation.joueur
        if joueur.categorie_reference_id == request.preparateur.categorie_id:
            participation.questionnaire = etat_questionnaire(
                seance.date,
                aujourdhui,
                joueur.categorie_reference.jours_questionnaire,
                recu=joueur.pk in ont_repondu,
            )
    return participations


def _page_seance(
    request: RequeteStaff,
    seance: Seance,
    grille: GrilleRpeForm | None = None,
    correction: bool = False,
) -> HttpResponse:
    """Brouillon ou correction : grille RPE, puis participants et annuaire.
    Séance validée, en lecture : RPE et charges calculées par le moteur."""
    participations = _participations(request, seance)
    edition = seance.statut == StatutSeance.BROUILLON or correction
    recherche = request.GET.get("q", "").strip()
    resultats = []
    if recherche and edition:
        resultats = list(
            annuaire(request.preparateur)
            .filter(Q(nom__icontains=recherche) | Q(prenom__icontains=recherche))
            .exclude(pk__in=[participation.joueur_id for participation in participations])[
                :RESULTATS_ANNUAIRE
            ]
        )
    if edition and grille is None:
        grille = GrilleRpeForm(participations=participations, correction=correction)
    # Charges calculées par le moteur (phase 3) : aucune formule n'est réécrite ici.
    charges = {} if edition else charges_de_seance(seance, participations, parametres())
    return render(
        request,
        "suivi/seance.html",
        {
            "rubrique": "seances",
            "seance": seance,
            "brouillon": seance.statut == StatutSeance.BROUILLON,
            "edition": edition,
            "correction": correction,
            "grille": grille,
            "participations": participations,
            "validees": [(p, charges[p.pk]) for p in participations] if not edition else [],
            "recherche": recherche,
            "resultats": resultats,
            "limite": RESULTATS_ANNUAIRE,
            # Champ de chaque colonne de RPE, son libellé, et sa forme courte sur téléphone.
            "colonnes": [
                ("rpe_cardio", "Cardio", "Card."),
                ("rpe_musculaire", "Musculaire", "Musc."),
                ("rpe_teta", "TETA", "TETA"),
            ],
        },
    )


@require_safe
def seance_detail(request: RequeteStaff, pk: int) -> HttpResponse:
    """Une séance : sa grille RPE tant qu'elle est en brouillon, ses charges une fois validée."""
    return _page_seance(request, _seance_organisee(request, pk))


@require_safe
def seance_corriger(request: RequeteStaff, pk: int) -> HttpResponse:
    """Correction directe d'une séance validée : elle reste validée (ADR-0008, US-06)."""
    seance = _seance_organisee(request, pk)
    if seance.statut != StatutSeance.VALIDEE:
        return redirect("seance", pk=pk)  # un brouillon se modifie sur sa propre page
    return _page_seance(request, seance, correction=True)


@require_POST
def seance_grille(request: RequeteStaff, pk: int) -> HttpResponse:
    """Brouillon (RPE facultatifs), validation (US-05) ou correction d'une séance validée,
    qui garde les trois RPE de chaque participant (US-06)."""
    seance = _seance_organisee(request, pk)
    correction = seance.statut == StatutSeance.VALIDEE
    valider = not correction and "valider" in request.POST
    grille = GrilleRpeForm(
        request.POST,
        participations=_participations(request, seance),
        valider=valider,
        correction=correction,
    )
    if not grille.is_valid():
        return _page_seance(request, seance, grille, correction=correction)
    champs = [champ for champ, _ in COLONNES_RPE]
    with transaction.atomic():
        for participation in grille.participations_modifiees():
            participation.updated_by = request.user
            participation.save(update_fields=[*champs, "updated_by", "updated_at"])
        seance.updated_by = request.user
        if valider:
            # Le déclencheur de l'ADR-0008 refuserait une participation incomplète.
            seance.statut = StatutSeance.VALIDEE
            seance.validated_at = timezone.now()
        seance.save()
    if correction:
        messages.success(
            request, "Les corrections sont enregistrées : les charges sont recalculées."
        )
    elif valider:
        messages.success(request, "La séance est validée : les charges sont calculées.")
    else:
        messages.success(request, "Le brouillon est enregistré.")
    return redirect("seance", pk=pk)


@require_http_methods(["GET", "HEAD", "POST"])
def seance_modifier(request: RequeteStaff, pk: int) -> HttpResponse:
    """Corrige la date, le type ou la durée ; la séance garde son statut (US-06)."""
    seance = _seance_organisee(request, pk)
    titre = seance.date
    form = SeanceEnteteForm(request.POST if request.method == "POST" else None, instance=seance)
    if form.is_valid():
        seance = form.save(commit=False)
        seance.updated_by = request.user
        seance.save()
        messages.success(request, "L’en-tête de la séance est modifié.")
        return redirect("seance", pk=pk)
    return render(
        request,
        "suivi/seance_modifier.html",
        {"rubrique": "seances", "form": form, "seance": seance, "titre": titre},
    )


@require_http_methods(["GET", "HEAD", "POST"])
def seance_supprimer(request: RequeteStaff, pk: int) -> HttpResponse:
    """Suppression confirmée : la séance et ses participations disparaissent (ADR-0008)."""
    seance = _seance_organisee(request, pk)
    if request.method == "POST":
        date = seance.date
        seance.delete()
        messages.success(request, f"La séance du {date:%d/%m/%Y} est supprimée.")
        return redirect("seances")
    participants = participations_visibles(request.preparateur).filter(seance=seance).count()
    return render(
        request,
        "suivi/seance_supprimer.html",
        {"rubrique": "seances", "seance": seance, "participants": participants},
    )


def _retour_a_la_seance(seance: Seance, recherche: str = "") -> HttpResponse:
    """Retour à la grille où l'on était : la page du brouillon, ou la correction."""
    vue = "seance" if seance.statut == StatutSeance.BROUILLON else "seance_corriger"
    url = reverse(vue, kwargs={"pk": seance.pk})
    return redirect(url + ("?" + urlencode({"q": recherche}) if recherche else ""))


def _toucher(seance: Seance, request: RequeteStaff) -> None:
    """Changer les participants modifie la séance : date et auteur enregistrés (ADR-0008)."""
    seance.updated_by = request.user
    seance.save(update_fields=["updated_by", "updated_at"])


@require_POST
def participant_ajouter(request: RequeteStaff, pk: int) -> HttpResponse:
    """Ajoute un joueur de l'annuaire : un absent revenu, ou un joueur invité (R24).

    Dans une séance validée, ses trois RPE sont saisis d'emblée (ADR-0008).
    """
    seance = _seance_organisee(request, pk)
    recherche = request.POST.get("q", "").strip()
    saisi = request.POST.get("joueur", "")
    # L'annuaire ne contient que des joueurs actifs : un archivé est introuvable ici.
    ligne = annuaire(request.preparateur).filter(pk=int(saisi)).first() if saisi.isdigit() else None
    if ligne is None:
        raise Http404
    nom = f"{ligne['prenom']} {ligne['nom']}"
    deja = participations_visibles(request.preparateur).filter(seance=seance, joueur_id=ligne["pk"])
    if deja.exists():
        messages.info(request, f"{nom} participe déjà à la séance.")
        return _retour_a_la_seance(seance, recherche)
    rpe = {}
    if seance.statut == StatutSeance.VALIDEE:
        saisie = RpeParticipantForm(request.POST)
        if not saisie.is_valid():
            messages.error(
                request,
                f"Pour ajouter {nom} à une séance validée, saisissez ses trois RPE, de 0 à 10.",
            )
            return _retour_a_la_seance(seance, recherche)
        rpe = saisie.cleaned_data
    with transaction.atomic():
        seance.participations.create(joueur_id=ligne["pk"], updated_by=request.user, **rpe)
        _toucher(seance, request)
    messages.success(request, f"{nom} est ajouté à la séance.")
    return _retour_a_la_seance(seance, recherche)


@require_POST
def participant_retirer(request: RequeteStaff, pk: int, participation_pk: int) -> HttpResponse:
    """Retire un absent ; ses éventuels RPE disparaissent avec sa participation."""
    seance = _seance_organisee(request, pk)
    visibles = participations_visibles(request.preparateur)
    participation = (
        visibles.filter(pk=participation_pk, seance=seance).select_related("joueur").first()
    )
    if participation is None:
        raise Http404
    if seance.statut == StatutSeance.VALIDEE and visibles.filter(seance=seance).count() == 1:
        messages.error(
            request,
            "Une séance validée garde au moins un participant : pour l’annuler, supprimez-la.",
        )
        return _retour_a_la_seance(seance)
    with transaction.atomic():
        participation.delete()
        _toucher(seance, request)
    messages.success(request, f"{participation.joueur} est retiré de la séance.")
    return _retour_a_la_seance(seance)


# --- Sensations d'un joueur : correction par le préparateur (F17) ----------------------

# Entrées par page de la liste des sensations d'un joueur.
ENTREES_PAR_PAGE = 30


def _entree_suivie(request: RequeteStaff, joueur: Joueur, pk: int) -> EntreeSensations:
    """Entrée *passée* d'un joueur suivi ; 404 pour toute autre, qu'elle existe ou non (A3).

    Celle du jour est au joueur, par son lien (R16) : le préparateur ne la corrige pas.
    """
    entree = (
        entrees_visibles(request.preparateur)
        .filter(pk=pk, joueur=joueur, date__lt=aujourd_hui())
        .first()
    )
    if entree is None:
        raise Http404
    return entree


@require_safe
def sensations_joueur(request: RequeteStaff, pk: int) -> HttpResponse:
    """Entrées de sensations d'un joueur suivi, des plus récentes aux plus anciennes."""
    joueur = _joueur_suivi(request, pk)
    entrees = (
        entrees_visibles(request.preparateur)
        .filter(joueur=joueur)
        .select_related("updated_by")
        .order_by("-date")
    )
    page = Paginator(entrees, ENTREES_PAR_PAGE).get_page(request.GET.get("page"))
    return render(
        request,
        "suivi/sensations_joueur.html",
        {"rubrique": "joueurs", "joueur": joueur, "page": page, "aujourdhui": aujourd_hui()},
    )


@require_http_methods(["GET", "HEAD", "POST"])
def entree_corriger(request: RequeteStaff, pk: int, entree_pk: int) -> HttpResponse:
    """Corrige les réponses d'une entrée passée ; sa date ne change pas (ADR-0008 Q3)."""
    joueur = _joueur_suivi(request, pk)
    entree = _entree_suivie(request, joueur, entree_pk)
    reponses = dict(entree.reponses.values_list("indicateur_id", "valeur"))
    formulaire = QuestionnaireForm(
        indicateurs_du_questionnaire(joueur),
        request.POST if request.method == "POST" else None,
        reponses=reponses,
        correction=True,
    )
    if request.method == "POST" and formulaire.is_valid():
        # Seules les réponses qui changent sont écrites : un envoi du formulaire tel quel
        # n'est pas une correction et ne laisse pas de trace.
        valeurs = {i: v for i, v in formulaire.valeurs().items() if reponses.get(i) != v}
        if valeurs:
            try:
                corriger_entree(entree, valeurs, request.user)
            except EntreeSupprimee:
                raise Http404 from None
            messages.success(
                request, f"L’entrée du {entree.date:%d/%m/%Y} de {joueur} est corrigée."
            )
        else:
            messages.info(request, "Aucune modification : les réponses sont inchangées.")
        return redirect("sensations_joueur", pk=joueur.pk)
    return render(
        request,
        "suivi/entree_corriger.html",
        {"rubrique": "joueurs", "joueur": joueur, "entree": entree, "formulaire": formulaire},
    )


@require_http_methods(["GET", "HEAD", "POST"])
def entree_supprimer(request: RequeteStaff, pk: int, entree_pk: int) -> HttpResponse:
    """Suppression confirmée d'une entrée passée, à la demande du joueur (ADR-0008 Q3)."""
    joueur = _joueur_suivi(request, pk)
    entree = _entree_suivie(request, joueur, entree_pk)
    if request.method == "POST":
        try:
            supprimer_entree(entree, request.user)
        except EntreeSupprimee:
            raise Http404 from None
        messages.success(request, f"L’entrée du {entree.date:%d/%m/%Y} de {joueur} est supprimée.")
        return redirect("sensations_joueur", pk=joueur.pk)
    return render(
        request,
        "suivi/entree_supprimer.html",
        {"rubrique": "joueurs", "joueur": joueur, "entree": entree},
    )
