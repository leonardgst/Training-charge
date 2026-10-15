from collections.abc import Callable
from typing import Any

from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse

from suivi.models import Preparateur

# Architecture, section 5 : tout vient de l'origine du site, rien en ligne. Scripts, styles,
# polices et requêtes retombent sur `default-src`.
POLITIQUE_DE_SECURITE_DU_CONTENU = "; ".join(
    [
        "default-src 'self'",
        # Pico CSS dessine ses icônes (listes, cases, champs invalides) en SVG intégrés.
        "img-src 'self' data:",
        "object-src 'none'",
        "base-uri 'none'",
        "form-action 'self'",
        "frame-ancestors 'none'",
    ]
)


class PolitiqueDeSecuriteDuContenuMiddleware:
    """Pose la politique de sécurité du contenu sur chaque réponse.

    Placé juste après `SecurityMiddleware` : il enveloppe toutes les autres couches, donc
    les redirections vers la connexion, les refus et les pages d'erreur la portent aussi.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        reponse = self.get_response(request)
        reponse.headers.setdefault("Content-Security-Policy", POLITIQUE_DE_SECURITE_DU_CONTENU)
        return reponse


class RequeteStaff(HttpRequest):
    """Requête d'une vue staff, après le passage de `ProfilPreparateurRequisMiddleware`."""

    user: User
    preparateur: Preparateur


class ProfilPreparateurRequisMiddleware:
    """Toute URL staff exige un profil préparateur (ADR-0005, couche 3).

    Sont exemptées : les vues de la liste blanche (`login_not_required`) et
    l'administration, qui exige le superutilisateur (`suivi.site_admin.SiteAdmin`).
    Un compte connecté sans profil préparateur reçoit un refus 403. Sinon, le profil est
    posé sur `request.preparateur`, avec sa catégorie : les vues et les gabarits du staff
    le lisent là.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        return self.get_response(request)

    def process_view(
        self,
        request: HttpRequest,
        view_func: Callable[..., HttpResponse],
        view_args: tuple[Any, ...],
        view_kwargs: dict[str, Any],
    ) -> HttpResponse | None:
        if getattr(view_func, "login_required", True) is False:
            return None
        if request.resolver_match and "admin" in request.resolver_match.app_names:
            return None
        pk = request.user.pk
        preparateur = (
            Preparateur.objects.select_related("categorie").filter(user_id=pk).first()
            if pk is not None
            else None
        )
        if preparateur is None:
            raise PermissionDenied
        request.preparateur = preparateur  # type: ignore[attr-defined]
        return None
