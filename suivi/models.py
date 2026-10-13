from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models.functions import Length, Trim
from django.db.models.lookups import GreaterThan

JOURS_SEMAINE = list(range(7))


def tous_les_jours() -> list[int]:
    return list(JOURS_SEMAINE)


class Categorie(models.Model):
    code = models.CharField(max_length=20, unique=True)
    libelle = models.CharField(max_length=100)
    # Jours de la semaine (0 = lundi) où le questionnaire de sensations est proposé.
    jours_questionnaire = ArrayField(models.SmallIntegerField(), default=tous_les_jours)
    active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(jours_questionnaire__contained_by=JOURS_SEMAINE),
                name="categorie_jours_questionnaire_valides",
            ),
            models.CheckConstraint(
                condition=GreaterThan(Length(Trim("code")), 0),
                name="categorie_code_non_vide",
            ),
        ]

    def __str__(self) -> str:
        return self.code


class Preparateur(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="preparateur"
    )
    categorie = models.ForeignKey(Categorie, on_delete=models.PROTECT, related_name="preparateurs")

    def __str__(self) -> str:
        return f"{self.user} ({self.categorie})"


class Joueur(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    date_naissance = models.DateField()
    categorie_reference = models.ForeignKey(
        Categorie, on_delete=models.PROTECT, related_name="joueurs"
    )
    # Archivé = ne fait plus partie du groupe ; données conservées (ADR-0009).
    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=GreaterThan(Length(Trim("nom")), 0), name="joueur_nom_non_vide"
            ),
            models.CheckConstraint(
                condition=GreaterThan(Length(Trim("prenom")), 0), name="joueur_prenom_non_vide"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.prenom} {self.nom}"
