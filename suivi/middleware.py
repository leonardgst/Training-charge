from collections.abc import Callable
from typing import Any

from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse

from suivi.models import Preparateur


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
