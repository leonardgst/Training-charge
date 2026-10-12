"""Routes du projet."""

from django.contrib import admin
from django.contrib.auth.decorators import login_not_required
from django.contrib.auth.views import LoginView
from django.urls import path
from django.views.generic import TemplateView

from suivi.views.sante import sante

urlpatterns = [
    path("", TemplateView.as_view(template_name="suivi/accueil.html"), name="accueil"),
    path(
        "connexion/",
        login_not_required(
            LoginView.as_view(
                template_name="suivi/connexion.html",
                redirect_authenticated_user=True,
            )
        ),
        name="connexion",
    ),
    path("sante/", sante, name="sante"),
    path("admin/", admin.site.urls),
]
