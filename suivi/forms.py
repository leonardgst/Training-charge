"""Formulaires de saisie du staff.

Chaque contrainte de la base est aussi vérifiée ici, pour un message lisible à la saisie
(cas D1) ; la base reste le dernier rempart.
"""

import datetime

from django import forms

from suivi.horloge import aujourd_hui
from suivi.models import Joueur


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
