"""Formulaires de saisie du staff.

Chaque contrainte de la base est aussi vérifiée ici, pour un message lisible à la saisie
(cas D1) ; la base reste le dernier rempart.
"""

import datetime
from typing import Any, cast

from django import forms
from django.db.models import QuerySet

from suivi.horloge import aujourd_hui
from suivi.models import DUREE_MAX, DUREE_MIN, Joueur, Seance, TypeSeance


class JoueurForm(forms.ModelForm):
    """Identité d'un joueur. La catégorie de référence est celle du préparateur : elle
    n'est jamais lue dans la requête, pas plus que l'archivage."""

    class Meta:
        model = Joueur
        fields = ["nom", "prenom", "date_naissance"]
        labels = {"nom": "Nom", "prenom": "Prénom", "date_naissance": "Date de naissance"}
        widgets = {
            "date_naissance": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }

    def clean_date_naissance(self) -> datetime.date:
        date_naissance: datetime.date = self.cleaned_data["date_naissance"]
        if date_naissance > aujourd_hui():
            raise forms.ValidationError("La date de naissance ne peut pas être dans le futur.")
        return date_naissance


class _ChoixJoueurs(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj: Joueur) -> str:
        return f"{obj.nom} {obj.prenom}"


class SeanceForm(forms.ModelForm):
    """En-tête d'une séance, saisi une seule fois, et ses participants (US-03).

    La catégorie organisatrice est celle du préparateur, posée par la vue. Les
    participants possibles sont les joueurs que la vue fournit : un identifiant hors de
    cette liste est refusé.
    """

    duree_min = forms.IntegerField(
        label="Durée (minutes)",
        min_value=DUREE_MIN,
        max_value=DUREE_MAX,
        widget=forms.NumberInput(attrs={"inputmode": "numeric"}),
    )
    participants = _ChoixJoueurs(
        queryset=Joueur.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Participants",
    )

    class Meta:
        model = Seance
        fields = ["date", "type", "duree_min"]
        labels = {"date": "Date", "type": "Type"}
        widgets = {"date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")}

    def __init__(self, *args: Any, joueurs: QuerySet[Joueur], **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        cast(_ChoixJoueurs, self.fields["participants"]).queryset = joueurs
        # Pas de choix vide : le type est l'une des quatre valeurs de la liste fermée.
        cast(forms.ChoiceField, self.fields["type"]).choices = TypeSeance.choices
