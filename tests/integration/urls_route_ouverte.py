"""Table des routes de test pour A2 : celle du projet, plus une route publique oubliée."""

from django.contrib.auth.decorators import login_not_required
from django.http import HttpRequest, HttpResponse
from django.urls import path

from config.urls import urlpatterns as urlpatterns_du_projet


@login_not_required
def fuite(request: HttpRequest) -> HttpResponse:
    return HttpResponse("donnée du staff")


urlpatterns = [*urlpatterns_du_projet, path("fuite/", fuite)]
