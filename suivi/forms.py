"""Formulaires de saisie du staff.

Chaque contrainte de la base est aussi vérifiée ici, pour un message lisible à la saisie
(cas D1) ; la base reste le dernier rempart.
"""

import datetime
import re
from collections.abc import Iterator, Sequence
from typing import Any, cast

from django import forms
from django.db.models import QuerySet

from suivi.horloge import aujourd_hui
from suivi.models import (
    DUREE_MAX,
    DUREE_MIN,
    RPE_MAX,
    RPE_MIN,
    Joueur,
    Participation,
    Seance,
    TypeSeance,
)


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


# Les trois RPE d'une participation, dans l'ordre des colonnes de la grille (US-04).
COLONNES_RPE = (("rpe_cardio", "cardio"), ("rpe_musculaire", "musculaire"), ("rpe_teta", "TETA"))
VALEUR_RPE = re.compile(rf"^(?:{'|'.join(str(v) for v in range(RPE_MIN, RPE_MAX + 1))})$")


def niveau_rpe(valeur: object) -> str | None:
    """Classe de couleur d'une case : la valeur si elle est dans l'échelle, sinon `invalide`.

    Même règle que `suivi/static/suivi/js/grille.js`, qui recolore la case pendant la frappe.
    """
    texte = "" if valeur is None else str(valeur).strip()
    if not texte:
        return None
    return texte if VALEUR_RPE.match(texte) else "invalide"


class GrilleRpeForm(forms.Form):
    """Trois RPE par participant, au clavier : facultatifs en brouillon, exigés pour valider.

    Une case par participation et par RPE, nommée `p<id>_<champ>`. La touche Tab suit
    l'ordre du document : cardio, musculaire, TETA, puis la ligne suivante.
    """

    def __init__(
        self,
        *args: Any,
        participations: Sequence[Participation],
        valider: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.participations = list(participations)
        self.valider = valider
        for participation in self.participations:
            for champ, libelle in COLONNES_RPE:
                nom = self.nom(participation, champ)
                initial = getattr(participation, champ)
                attrs = {
                    "class": "rpe",
                    "inputmode": "numeric",
                    "pattern": VALEUR_RPE.pattern.strip("^$"),
                    "maxlength": "2",
                    "autocomplete": "off",
                    "aria-label": f"RPE {libelle} de {participation.joueur}",
                }
                niveau = niveau_rpe(self.data.get(nom) if self.is_bound else initial)
                if niveau:
                    attrs["data-niveau"] = niveau
                self.fields[nom] = forms.IntegerField(
                    required=False,
                    min_value=RPE_MIN,
                    max_value=RPE_MAX,
                    initial=initial,
                    label=f"RPE {libelle} de {participation.joueur}",
                    widget=forms.TextInput(attrs=attrs),
                )

    @staticmethod
    def nom(participation: Participation, champ: str) -> str:
        return f"p{participation.pk}_{champ}"

    def lignes(self) -> Iterator[tuple[Participation, list[forms.BoundField]]]:
        for participation in self.participations:
            yield participation, [self[self.nom(participation, c)] for c, _ in COLONNES_RPE]

    def clean(self) -> dict[str, Any]:
        donnees = self.cleaned_data
        if any(nom not in self.data for nom in self.fields):
            raise forms.ValidationError(
                "Les participants ont changé depuis l’ouverture de la grille : rechargez la page."
            )
        if self.valider:
            if not self.participations:
                raise forms.ValidationError("Une séance sans participant ne se valide pas.")
            vides = [
                nom for nom in self.fields if nom not in self.errors and donnees.get(nom) is None
            ]
            for nom in vides:
                self.add_error(nom, forms.ValidationError("Obligatoire.", code="manquant"))
            if vides:
                raise forms.ValidationError(
                    "La validation exige les trois RPE de chaque participant : "
                    f"{len(vides)} case(s) vide(s). "
                    "Enregistrez le brouillon pour terminer plus tard."
                )
        return donnees

    def erreurs_de_cases(self) -> list[str]:
        """Valeurs refusées, case par case ; les cases vides à la validation sont comptées
        par le message général et seulement signalées sur la grille."""
        return [
            f"{self.fields[nom].label} : {erreur.messages[0]}"
            for nom, erreurs in self.errors.as_data().items()
            if nom in self.fields
            for erreur in erreurs
            if erreur.code != "manquant"
        ]

    def participations_modifiees(self) -> list[Participation]:
        """Participations dont au moins un RPE change, valeurs posées (sans enregistrer)."""
        modifiees = []
        for participation in self.participations:
            avant = [getattr(participation, champ) for champ, _ in COLONNES_RPE]
            apres = [self.cleaned_data[self.nom(participation, champ)] for champ, _ in COLONNES_RPE]
            if avant != apres:
                for (champ, _), valeur in zip(COLONNES_RPE, apres, strict=True):
                    setattr(participation, champ, valeur)
                modifiees.append(participation)
        return modifiees
