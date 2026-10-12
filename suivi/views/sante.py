from django.contrib.auth.decorators import login_not_required
from django.http import HttpRequest, HttpResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_safe


@login_not_required
@require_safe
@never_cache
def sante(request: HttpRequest) -> HttpResponse:
    """Contrôle de santé : l'application répond. N'interroge pas la base."""
    return HttpResponse("ok", content_type="text/plain")
