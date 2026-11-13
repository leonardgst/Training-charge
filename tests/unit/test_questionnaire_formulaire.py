"""Formulaire du questionnaire, sans base de données (D1)."""

import datetime

from suivi.forms import QuestionnaireForm, nom_du_champ
from suivi.models import Indicateur

JOUR = "2026-11-13"


def _note(pk: int, borne_min: int = 0, borne_max: int = 10) -> Indicateur:
    return Indicateur(
        pk=pk,
        code=f"n{pk}",
        libelle=f"Note {pk}",
        type="note",
        borne_min=borne_min,
        borne_max=borne_max,
    )


def _heure(pk: int) -> Indicateur:
    return Indicateur(
        pk=pk, code=f"h{pk}", libelle=f"Heure {pk}", type="heure", borne_min=0, borne_max=1439
    )


def test_les_bornes_de_chaque_indicateur_sont_celles_du_formulaire() -> None:
    indicateurs = [_note(1), _note(2, borne_min=1, borne_max=5)]

    def valide(a: str, b: str) -> bool:
        return QuestionnaireForm(indicateurs, {"date": JOUR, "i1": a, "i2": b}).is_valid()

    assert valide("0", "1")
    assert valide("10", "5")
    assert not valide("11", "3")
    assert not valide("-1", "3")
    assert not valide("5", "0")
    assert not valide("5", "6")


def test_l_heure_est_convertie_en_minutes_depuis_minuit() -> None:
    formulaire = QuestionnaireForm([_heure(3)], {"date": JOUR, "i3": "23:59"})

    assert formulaire.is_valid()
    assert formulaire.valeurs() == {3: 1439}


def test_une_heure_invalide_ou_vide_est_refusee() -> None:
    for saisie in ("24:00", "12:60", "", "tard"):
        assert not QuestionnaireForm([_heure(3)], {"date": JOUR, "i3": saisie}).is_valid(), saisie


def test_les_reponses_existantes_preremplissent_les_champs() -> None:
    indicateurs = [_note(1), _heure(2)]

    formulaire = QuestionnaireForm(indicateurs, reponses={1: 7, 2: 75})

    assert formulaire.fields[nom_du_champ(indicateurs[0])].initial == 7
    assert formulaire.fields[nom_du_champ(indicateurs[1])].initial == datetime.time(1, 15)


def test_un_champ_inconnu_est_ignore() -> None:
    formulaire = QuestionnaireForm([_note(1)], {"date": JOUR, "i1": "4", "i99": "7"})

    assert formulaire.is_valid()
    assert formulaire.valeurs() == {1: 4}


def test_en_correction_il_n_y_a_pas_de_date_et_un_champ_vide_est_omis() -> None:
    formulaire = QuestionnaireForm([_note(1), _heure(2)], {"i1": "4", "i2": ""}, correction=True)

    assert "date" not in formulaire.fields
    assert formulaire.is_valid()
    assert formulaire.valeurs() == {1: 4}


def test_en_correction_une_valeur_hors_echelle_reste_refusee() -> None:
    assert not QuestionnaireForm([_note(1)], {"i1": "11"}, correction=True).is_valid()
    assert not QuestionnaireForm([_heure(2)], {"i2": "24:00"}, correction=True).is_valid()
