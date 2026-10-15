"""Routes du projet."""

from django.contrib import admin
from django.contrib.auth.decorators import login_not_required
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path
from django.views.generic import TemplateView

from suivi.views import staff
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
    path("deconnexion/", LogoutView.as_view(), name="deconnexion"),
    path("joueurs/", staff.joueurs, name="joueurs"),
    path("joueurs/nouveau/", staff.joueur_creer, name="joueur_creer"),
    path("joueurs/<int:pk>/modifier/", staff.joueur_modifier, name="joueur_modifier"),
    path("joueurs/<int:pk>/archiver/", staff.joueur_archiver, name="joueur_archiver"),
    path("joueurs/<int:pk>/reactiver/", staff.joueur_reactiver, name="joueur_reactiver"),
    path("seances/", staff.seances, name="seances"),
    path("seances/nouvelle/", staff.seance_creer, name="seance_creer"),
    path("seances/<int:pk>/", staff.seance_detail, name="seance"),
    path("seances/<int:pk>/grille/", staff.seance_grille, name="seance_grille"),
    path("seances/<int:pk>/corriger/", staff.seance_corriger, name="seance_corriger"),
    path("seances/<int:pk>/modifier/", staff.seance_modifier, name="seance_modifier"),
    path("seances/<int:pk>/supprimer/", staff.seance_supprimer, name="seance_supprimer"),
    path(
        "seances/<int:pk>/participants/ajouter/",
        staff.participant_ajouter,
        name="participant_ajouter",
    ),
    path(
        "seances/<int:pk>/participations/<int:participation_pk>/retirer/",
        staff.participant_retirer,
        name="participant_retirer",
    ),
    path("sante/", sante, name="sante"),
    path("admin/", admin.site.urls),
]
