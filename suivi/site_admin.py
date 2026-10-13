from django.contrib.admin import AdminSite
from django.contrib.admin.apps import AdminConfig
from django.http import HttpRequest


class SiteAdmin(AdminSite):
    """Administration réservée au superutilisateur (ADR-0005).

    `is_staff` ouvre l'administration par défaut ; ici elle exige `is_superuser`, pour
    qu'un préparateur n'y entre jamais, quel que soit son drapeau `is_staff`.
    """

    def has_permission(self, request: HttpRequest) -> bool:
        user = request.user
        return bool(user.is_active and user.is_superuser)


class AdminSuperutilisateurConfig(AdminConfig):
    default_site = "suivi.site_admin.SiteAdmin"
