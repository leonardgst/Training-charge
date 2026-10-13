from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models.functions import Length, Trim
from django.db.models.lookups import GreaterThan

JOURS_SEMAINE = list(range(7))

# Échelles figées en base ; un changement passe par une migration (ADR-0007).
RPE_MIN = 0
RPE_MAX = 10
DUREE_MIN = 1
DUREE_MAX = 300


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


class TypeSeance(models.TextChoices):
    FOOT = "foot", "Foot"
    MUSCULATION = "musculation", "Musculation"
    YOGA = "yoga", "Yoga"
    AUTRE = "autre", "Autre"


class StatutSeance(models.TextChoices):
    BROUILLON = "brouillon", "Brouillon"
    VALIDEE = "validee", "Validée"


class Seance(models.Model):
    categorie_organisatrice = models.ForeignKey(
        Categorie, on_delete=models.PROTECT, related_name="seances"
    )
    date = models.DateField()
    type = models.CharField(max_length=20, choices=TypeSeance.choices)
    duree_min = models.SmallIntegerField()
    statut = models.CharField(
        max_length=20, choices=StatutSeance.choices, default=StatutSeance.BROUILLON
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    validated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(duree_min__gte=DUREE_MIN, duree_min__lte=DUREE_MAX),
                name="seance_duree_dans_la_plage",
            ),
            models.CheckConstraint(
                condition=models.Q(type__in=TypeSeance.values), name="seance_type_valide"
            ),
            models.CheckConstraint(
                condition=models.Q(statut__in=StatutSeance.values), name="seance_statut_valide"
            ),
            models.CheckConstraint(
                condition=models.Q(statut="validee", validated_at__isnull=False)
                | models.Q(statut="brouillon", validated_at__isnull=True),
                name="seance_validated_at_coherent",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.get_type_display()} du {self.date} ({self.categorie_organisatrice})"


class Participation(models.Model):
    seance = models.ForeignKey(Seance, on_delete=models.CASCADE, related_name="participations")
    joueur = models.ForeignKey(Joueur, on_delete=models.CASCADE, related_name="participations")
    # Facultatifs tant que la séance est en brouillon ; un déclencheur les exige
    # une fois la séance validée (ADR-0008).
    rpe_cardio = models.SmallIntegerField(null=True, blank=True)
    rpe_musculaire = models.SmallIntegerField(null=True, blank=True)
    rpe_teta = models.SmallIntegerField(null=True, blank=True)
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
            models.UniqueConstraint(fields=["seance", "joueur"], name="participation_unique"),
            *(
                models.CheckConstraint(
                    condition=models.Q(**{f"{rpe}__isnull": True})
                    | models.Q(**{f"{rpe}__gte": RPE_MIN, f"{rpe}__lte": RPE_MAX}),
                    name=f"participation_{rpe}_dans_la_plage",
                )
                for rpe in ("rpe_cardio", "rpe_musculaire", "rpe_teta")
            ),
        ]

    def __str__(self) -> str:
        return f"{self.joueur} à {self.seance}"
