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

from suivi.models import Joueur, LienJoueur

# 32 octets d'aléa : 256 bits, 43 caractères d'un alphabet sûr dans une adresse.
OCTETS_DU_JETON = 32


def generer_jeton() -> str:
    return secrets.token_urlsafe(OCTETS_DU_JETON)


def empreinte(jeton: str) -> str:
    """SHA-256 hexadécimal. Un hachage lent n'apporte rien sur un secret de 256 bits."""
    return hashlib.sha256(jeton.encode()).hexdigest()


def revoquer_liens(joueur: Joueur) -> int:
    """Ferme le lien actif du joueur, s'il y en a un. Renvoie le nombre de liens fermés."""
    return LienJoueur.objects.filter(joueur=joueur, revoked_at__isnull=True).update(
        revoked_at=timezone.now()
    )


def creer_lien(joueur: Joueur, auteur: User) -> str:
    """Révoque le lien actif puis en crée un nouveau, dans une seule transaction.

    Renvoie le jeton en clair, qui n'existera plus nulle part ensuite.
    """
    jeton = generer_jeton()
    with transaction.atomic():
        revoquer_liens(joueur)
        LienJoueur.objects.create(joueur=joueur, token_hash=empreinte(jeton), created_by=auteur)
    return jeton


def qr_data_uri(adresse: str) -> str:
    """QR code de l'adresse en image SVG intégrée : aucune ressource tierce, aucune route."""
    return segno.make(adresse, error="m").svg_data_uri(scale=6, border=2, xmldecl=False)
