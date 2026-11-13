"""Questionnaire du jour d'un joueur : indicateurs proposés, entrée du jour, enregistrement.

Seul module, avec `suivi/liens.py`, que la vue du lien joueur interroge : elle n'atteint
que les indicateurs de la catégorie de référence du joueur et son entrée du jour (A4).
"""

import datetime
import logging

from django.contrib.auth.models import User
from django.db import transaction

from suivi.models import EntreeSensations, Indicateur, Joueur, LienJoueur, Reponse


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


class LienPerime(Exception):  # noqa: N818
    """Le lien a été révoqué ou le joueur archivé pendant l'envoi."""


def enregistrer_entree(
    joueur: Joueur, jour: datetime.date, valeurs: dict[int, int], empreinte_du_lien: str
) -> None:
    """Crée l'entrée du jour ou modifie celle qui existe (D2) ; `valeurs` : clé -> valeur.

    Le joueur est verrouillé : deux envois simultanés se suivent. L'auteur reste nul, car
    c'est le joueur lui-même (ADR-0008) : une modification l'y remet. Le lien est revérifié
    une fois le verrou pris (`LienPerime`). Une réponse à un indicateur désactivé depuis
    n'est jamais supprimée (ADR-0016).
    """
    with transaction.atomic():
        verrouille = Joueur.objects.select_for_update().get(pk=joueur.pk)
        if (
            not verrouille.actif
            or not LienJoueur.objects.filter(
                joueur=verrouille, token_hash=empreinte_du_lien, revoked_at__isnull=True
            ).exists()
        ):
            raise LienPerime
        entree, creee = EntreeSensations.objects.get_or_create(joueur=joueur, date=jour)
        if not creee:
            entree.updated_by = None
            entree.save()  # renouvelle `updated_at`
        for indicateur_id, valeur in valeurs.items():
            Reponse.objects.update_or_create(
                entree=entree, indicateur_id=indicateur_id, defaults={"valeur": valeur}
            )


audit = logging.getLogger("suivi.audit")


class EntreeSupprimee(Exception):  # noqa: N818
    """L'entrée a été supprimée pendant que le préparateur la corrigeait."""


def _entree_verrouillee(entree: EntreeSensations) -> EntreeSensations:
    """Verrouille le joueur puis relit l'entrée : elle a pu être supprimée entre-temps."""
    Joueur.objects.select_for_update().get(pk=entree.joueur_id)
    relue = EntreeSensations.objects.filter(pk=entree.pk).first()
    if relue is None:
        raise EntreeSupprimee
    return relue


def corriger_entree(entree: EntreeSensations, valeurs: dict[int, int], auteur: User) -> None:
    """Le préparateur corrige les réponses d'une entrée passée (F17, ADR-0008 Q3).

    La date de l'entrée ne change pas ; `updated_at` et `updated_by` disent qui a corrigé et
    quand. Un indicateur sans réponse dans l'entrée en reçoit une ; aucune réponse n'est
    supprimée. L'appelant a vérifié que l'entrée est dans son périmètre ; `EntreeSupprimee`
    si elle a disparu entre-temps.
    """
    with transaction.atomic():
        entree = _entree_verrouillee(entree)
        for indicateur_id, valeur in valeurs.items():
            Reponse.objects.update_or_create(
                entree=entree, indicateur_id=indicateur_id, defaults={"valeur": valeur}
            )
        entree.updated_by = auteur
        entree.save()


def supprimer_entree(entree: EntreeSensations, auteur: User) -> None:
    """Supprime une entrée passée et ses réponses, à la demande du joueur (ADR-0008 Q3).

    Il n'y a pas d'historique des valeurs en V1 : la suppression est tracée au journal
    `suivi.audit`, par clé et sans nom de joueur, une fois la suppression validée.
    L'appelant a vérifié le périmètre ; `EntreeSupprimee` si l'entrée a déjà disparu.
    """
    with transaction.atomic():
        entree = _entree_verrouillee(entree)
        joueur_id, jour = entree.joueur_id, entree.date
        entree.delete()
    audit.info(
        "Entrée de sensations supprimée : joueur=%s date=%s par=%s",
        joueur_id,
        jour.isoformat(),
        auteur.get_username(),
    )
