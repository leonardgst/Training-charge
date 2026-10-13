"""Couche d'accès du staff : seul point d'entrée des requêtes d'une vue staff (ADR-0005).

Chaque fonction reçoit le préparateur connecté et renvoie le périmètre qu'il a le droit
de voir. Une vue qui interrogerait directement `Joueur.objects` contournerait ce
périmètre : un test le vérifie.
"""

from typing import Any

from django.db.models import Q, QuerySet

from suivi.models import EntreeSensations, Joueur, Participation, Preparateur, Seance


def joueurs_suivis(preparateur: Preparateur) -> QuerySet[Joueur]:
    """Joueurs dont la catégorie de référence est celle du préparateur."""
    return Joueur.objects.filter(categorie_reference=preparateur.categorie)


def annuaire(preparateur: Preparateur) -> QuerySet[Joueur, Any]:
    """Joueurs actifs de toutes les catégories, limités au nom, au prénom et à la catégorie.

    Sert à ajouter un joueur invité à une séance : aucune autre donnée n'est lisible.
    """
    return (
        Joueur.objects.filter(actif=True)
        .order_by("nom", "prenom", "pk")
        .values("pk", "nom", "prenom", "categorie_reference__code")
    )


def seances_organisees(preparateur: Preparateur) -> QuerySet[Seance]:
    """Séances organisées par la catégorie du préparateur."""
    return Seance.objects.filter(categorie_organisatrice=preparateur.categorie)


def participations_visibles(preparateur: Preparateur) -> QuerySet[Participation]:
    """Participations de ses joueurs suivis, et participations aux séances qu'il organise.

    La seconde moitié couvre le joueur invité : le préparateur organisateur lit sa
    participation à ses séances, sans voir le reste de son historique.
    """
    return Participation.objects.filter(
        Q(joueur__categorie_reference=preparateur.categorie)
        | Q(seance__categorie_organisatrice=preparateur.categorie)
    )


def entrees_visibles(preparateur: Preparateur) -> QuerySet[EntreeSensations]:
    """Entrées de sensations de ses joueurs suivis (jamais celles d'un joueur invité)."""
    return EntreeSensations.objects.filter(joueur__categorie_reference=preparateur.categorie)
