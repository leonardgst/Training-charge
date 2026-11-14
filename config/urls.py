"""Routes du projet."""

from django.contrib import admin
from django.contrib.auth.decorators import login_not_required
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path
from django.views.generic import TemplateView

from suivi.views import forme, questionnaire, staff
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
    path("forme/", forme.forme_actuelle, name="forme_actuelle"),
    path("joueurs/", staff.joueurs, name="joueurs"),
    path("joueurs/nouveau/", staff.joueur_creer, name="joueur_creer"),
    path("joueurs/<int:pk>/modifier/", staff.joueur_modifier, name="joueur_modifier"),
    path("joueurs/<int:pk>/archiver/", staff.joueur_archiver, name="joueur_archiver"),
    path("joueurs/<int:pk>/reactiver/", staff.joueur_reactiver, name="joueur_reactiver"),
    path("joueurs/<int:pk>/lien/generer/", staff.lien_generer, name="lien_generer"),
    path("joueurs/<int:pk>/lien/revoquer/", staff.lien_revoquer, name="lien_revoquer"),
    path("joueurs/<int:pk>/sensations/", staff.sensations_joueur, name="sensations_joueur"),
    path(
        "joueurs/<int:pk>/sensations/<int:entree_pk>/corriger/",
        staff.entree_corriger,
        name="entree_corriger",
    ),
    path(
        "joueurs/<int:pk>/sensations/<int:entree_pk>/supprimer/",
        staff.entree_supprimer,
        name="entree_supprimer",
    ),
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
    # Sans barre finale : une redirection exposerait le jeton dans une adresse.
    path("q/<str:jeton>", questionnaire.questionnaire, name="questionnaire"),
    path("sante/", sante, name="sante"),
    path("admin/", admin.site.urls),
]
