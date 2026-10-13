from typing import Any

from django.contrib import admin
from django.http import HttpRequest

from suivi.models import Categorie, Indicateur, Joueur, Preparateur


@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ("code", "libelle", "active")


@admin.register(Preparateur)
class PreparateurAdmin(admin.ModelAdmin):
    list_display = ("user", "categorie")


@admin.register(Joueur)
class JoueurAdmin(admin.ModelAdmin):
    list_display = ("nom", "prenom", "categorie_reference", "actif")
    list_filter = ("categorie_reference", "actif")
    search_fields = ("nom", "prenom")
    readonly_fields = ("created_at", "updated_at", "updated_by")

    def save_model(self, request: HttpRequest, obj: Joueur, form: Any, change: bool) -> None:
        obj.updated_by = request.user  # type: ignore[assignment]
        super().save_model(request, obj, form, change)


@admin.register(Indicateur)
class IndicateurAdmin(admin.ModelAdmin):
    list_display = ("categorie", "ordre", "code", "libelle", "type", "poids", "actif")
    list_filter = ("categorie", "actif")
