"""Questionnaire du jour d'un joueur : indicateurs proposés, entrée du jour, enregistrement.

Seul module, avec `suivi/liens.py`, que la vue du lien joueur interroge : elle n'atteint
que les indicateurs de la catégorie de référence du joueur et son entrée du jour (A4).
"""

import datetime

from django.db import transaction

from suivi.models import EntreeSensations, Indicateur, Joueur, Reponse


def indicateurs_du_questionnaire(joueur: Joueur) -> list[Indicateur]:
    """Indicateurs actifs de la catégorie de référence du joueur, dans l'ordre d'affichage."""
    return list(
        Indicateur.objects.filter(categorie=joueur.categorie_reference, actif=True).order_by(
            "ordre", "pk"
        )
    )


def reponses_du_jour(joueur: Joueur, jour: datetime.date) -> dict[int, int]:
    """Valeur déjà donnée à chaque indicateur (par clé) dans l'entrée du joueur de ce jour."""
    return dict(
        Reponse.objects.filter(entree__joueur=joueur, entree__date=jour).values_list(
            "indicateur_id", "valeur"
        )
    )


def enregistrer_entree(joueur: Joueur, jour: datetime.date, valeurs: dict[int, int]) -> None:
    """Crée l'entrée du jour ou modifie celle qui existe (D2) ; `valeurs` : clé -> valeur.

    Le joueur est verrouillé : deux envois simultanés se suivent. L'auteur reste nul, car
    c'est le joueur lui-même (ADR-0008). Une réponse à un indicateur désactivé depuis
    n'est jamais supprimée (ADR-0016).
    """
    with transaction.atomic():
        Joueur.objects.select_for_update().get(pk=joueur.pk)
        entree, creee = EntreeSensations.objects.get_or_create(joueur=joueur, date=jour)
        if not creee:
            entree.save()  # renouvelle `updated_at`
        for indicateur_id, valeur in valeurs.items():
            Reponse.objects.update_or_create(
                entree=entree, indicateur_id=indicateur_id, defaults={"valeur": valeur}
            )
