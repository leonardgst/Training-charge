"""Liens joueurs : jeton, empreinte, création, révocation et QR code (US-07, ADR-0006).

Le jeton en clair n'est jamais stocké, journalisé ni mis en session : `creer_lien` le
renvoie une seule fois à la vue, qui le montre dans sa réponse.
"""

import hashlib
import secrets

import segno
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from suivi.models import Joueur, LienJoueur

# 32 octets d'aléa : 256 bits, 43 caractères d'un alphabet sûr dans une adresse.
OCTETS_DU_JETON = 32


def generer_jeton() -> str:
    return secrets.token_urlsafe(OCTETS_DU_JETON)


def empreinte(jeton: str) -> str:
    """SHA-256 hexadécimal. Un hachage lent n'apporte rien sur un secret de 256 bits."""
    return hashlib.sha256(jeton.encode()).hexdigest()


class JoueurArchive(Exception):  # noqa: N818
    """Le joueur a quitté le groupe : aucun lien ne peut lui être créé."""


def revoquer_liens(joueur: Joueur) -> int:
    """Ferme le lien actif du joueur, s'il y en a un. Renvoie le nombre de liens fermés.

    Contrat : l'appelant a déjà vérifié que le joueur est dans son périmètre
    (`suivi.acces.joueurs_suivis`) ; l'administration, elle, voit tous les joueurs.
    """
    return LienJoueur.objects.filter(joueur=joueur, revoked_at__isnull=True).update(
        revoked_at=timezone.now()
    )


def archiver_joueur(joueur: Joueur, auteur: User) -> None:
    """Départ du groupe : archive le joueur et révoque son lien, dans une seule transaction.

    Le verrou du joueur l'ordonne avec une création de lien simultanée (ADR-0006, ADR-0009).
    """
    with transaction.atomic():
        verrouille = Joueur.objects.select_for_update().get(pk=joueur.pk)
        verrouille.actif = False
        verrouille.updated_by = auteur
        verrouille.save()
        revoquer_liens(verrouille)
    joueur.actif = False
    joueur.updated_by = auteur


@sensitive_variables("jeton")
def creer_lien(joueur: Joueur, auteur: User) -> str:
    """Révoque le lien actif puis en crée un nouveau, dans une seule transaction.

    Le joueur est verrouillé : deux demandes simultanées (double appui) se suivent au lieu
    de se heurter à l'index unique, et un joueur archivé entre-temps est refusé.
    Renvoie le jeton en clair, qui n'existera plus nulle part ensuite.
    """
    jeton = generer_jeton()
    with transaction.atomic():
        verrouille = Joueur.objects.select_for_update().get(pk=joueur.pk)
        if not verrouille.actif:
            raise JoueurArchive(str(verrouille))
        revoquer_liens(verrouille)
        LienJoueur.objects.create(joueur=verrouille, token_hash=empreinte(jeton), created_by=auteur)
    return jeton


@sensitive_variables("adresse")
def qr_data_uri(adresse: str) -> str:
    """QR code de l'adresse en image SVG intégrée : aucune ressource tierce, aucune route."""
    return segno.make_qr(adresse, error="m").svg_data_uri(scale=6, border=2, xmldecl=False)


@sensitive_variables("jeton")
def joueur_du_lien(jeton: str) -> Joueur | None:
    """Joueur actif désigné par un jeton non révoqué ; `None` dans tous les autres cas.

    Un jeton inconnu, révoqué, régénéré ou d'un joueur archivé donnent le même résultat (A5).
    """
    lien = (
        LienJoueur.objects.select_related("joueur__categorie_reference")
        .filter(token_hash=empreinte(jeton), revoked_at__isnull=True, joueur__actif=True)
        .first()
    )
    return lien.joueur if lien else None
