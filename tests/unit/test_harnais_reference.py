"""Le harnais du jeu de référence se teste lui-même, sur un cas fictif (PR 3.1)."""

import datetime
from pathlib import Path

import pytest

from tests.reference.harnais import (
    Attendu,
    CasAbsent,
    ErreurFormat,
    Resultat,
    comparer,
    lire_cas,
    trouver_dossier,
    verifier_coherence,
)
from tests.reference.synthese import ecrire_cas

JOUR = datetime.date(2026, 1, 5)
ATT = "joueur,date,grandeur,valeur,etat\n"
PART = "seance_id,joueur,rpe_cardio,rpe_musculaire,rpe_teta\n"
SEA = "id,date,categorie,type,duree_min,statut\n"
IND = "categorie,code,type,borne_min,borne_max,sens,poids,inclus_score\n"
REP = "joueur,date,indicateur,valeur\n"


def _attendu(grandeur: str, valeur: float | None, etat: str = "ok") -> Attendu:
    return Attendu("J1", JOUR, grandeur, valeur, etat)


def _obtenu(
    grandeur: str, valeur: float | None, etat: str = "ok"
) -> dict[tuple[str, datetime.date, str], Resultat]:
    return {("J1", JOUR, grandeur): Resultat(valeur, etat)}


def test_lecture_d_un_cas_complet(tmp_path: Path) -> None:
    cas = lire_cas(ecrire_cas(tmp_path / "C00-test"))
    verifier_coherence(cas)
    assert cas.joueurs == {"J1": "U19", "J2": "U19"}
    assert [s.statut for s in cas.seances] == ["validee", "brouillon"]
    assert cas.participations[2].rpe_musculaire is None
    assert cas.parametres == {"facteur_echelle_charge": 1.0}
    assert cas.dates_calcul == (JOUR,)
    assert cas.attendu[1].valeur is None


def test_fichier_absent_est_simplement_omis(tmp_path: Path) -> None:
    cas = lire_cas(ecrire_cas(tmp_path / "C00-test", **{"reponses.csv": None, "attendu.csv": None}))
    assert cas.reponses == ()
    assert cas.attendu == ()


@pytest.mark.parametrize(
    ("remplacement", "message"),
    [
        ({"seances.csv": "id,date\nS1,2026-01-05\n"}, "colonnes attendues"),
        ({"cas.toml": None}, "fichier absent"),
        (
            {"attendu.csv": ATT + "J1,2026-01-05,charge_jour,,ok\n"},
            "si et seulement si",
        ),
        (
            {"attendu.csv": ATT + "J1,2026-01-05,charge_jour,3,non_calculable\n"},
            "si et seulement si",
        ),
        (
            {"attendu.csv": ATT + "J1,2026-01-05,vitesse,3,ok\n"},
            "grandeur inconnue",
        ),
        (
            {"attendu.csv": ATT + "J1,2026-01-05,charge_jour,3,bof\n"},
            "état inconnu",
        ),
        (
            {"attendu.csv": ATT + "J1,2026-01-05,charge_jour,trois,ok\n"},
            "nombre attendu",
        ),
        (
            {"attendu.csv": ATT + "J1,hier,charge_jour,3,ok\n"},
            "date ISO",
        ),
        (
            {"seances.csv": SEA + "S1,2026-01-05,U19,foot,soixante,validee\n"},
            "entier attendu",
        ),
        (
            {"indicateurs.csv": IND + "U19,f,note,1,5,bas_bon,1,oui\n"},
            "`true` ou `false`",
        ),
    ],
)
def test_format_invalide_refuse(
    tmp_path: Path, remplacement: dict[str, str | None], message: str
) -> None:
    with pytest.raises(ErreurFormat, match=message):
        verifier_coherence(lire_cas(ecrire_cas(tmp_path / "C00-test", **remplacement)))


@pytest.mark.parametrize(
    ("remplacement", "message"),
    [
        (
            {"participations.csv": PART + "S9,J1,1,1,1\n"},
            "séance inconnue",
        ),
        (
            {"participations.csv": PART + "S1,J9,1,1,1\n"},
            "joueur inconnu",
        ),
        (
            {"reponses.csv": REP + "J9,2026-01-05,fatigue,3\n"},
            "joueur inconnu",
        ),
        (
            {"reponses.csv": REP + "J1,2026-01-05,humeur,3\n"},
            "indicateur inconnu",
        ),
        (
            {"attendu.csv": ATT + "J9,2026-01-05,charge_jour,3,ok\n"},
            "joueur inconnu",
        ),
        (
            {
                "attendu.csv": ATT + ""
                "J1,2026-01-05,charge_jour,3,ok\nJ1,2026-01-05,charge_jour,4,ok\n"
            },
            "en double",
        ),
    ],
)
def test_incoherence_entre_fichiers_refusee(
    tmp_path: Path, remplacement: dict[str, str | None], message: str
) -> None:
    with pytest.raises(ErreurFormat, match=message):
        verifier_coherence(lire_cas(ecrire_cas(tmp_path / "C00-test", **remplacement)))


def test_reprend_les_entrees_d_un_autre_cas(tmp_path: Path) -> None:
    ecrire_cas(tmp_path / "C06-base")
    ecrire_cas(
        tmp_path / "C14-echelle",
        **{
            "cas.toml": 'reprend = "C06"\n\n[parametres]\nfacteur_echelle_charge = 7.0\n',
            "joueurs.csv": None,
            "seances.csv": None,
            "participations.csv": None,
            "indicateurs.csv": None,
            "reponses.csv": None,
            "attendu.csv": ATT + "J1,2026-01-05,charge_jour,2100.0,ok\n",
        },
    )
    cas = lire_cas(tmp_path / "C14-echelle")
    assert len(cas.seances) == 2
    assert cas.parametres == {"facteur_echelle_charge": 7.0}
    assert cas.attendu[0].valeur == 2100.0


def test_trouver_dossier_par_prefixe(tmp_path: Path) -> None:
    (tmp_path / "C01-simple").mkdir()
    assert trouver_dossier("C01", tmp_path).name == "C01-simple"
    with pytest.raises(CasAbsent):
        trouver_dossier("C02", tmp_path)
    (tmp_path / "C01-autre").mkdir()
    with pytest.raises(ErreurFormat, match="plusieurs dossiers"):
        trouver_dossier("C01", tmp_path)


def test_une_charge_se_compare_en_relatif() -> None:
    attendu = [_attendu("charge_jour", 1000.0)]
    assert comparer(attendu, _obtenu("charge_jour", 1000.0 + 0.9e-6)) == []
    assert comparer(attendu, _obtenu("charge_jour", 1000.0 + 1.1e-6)) != []


def test_un_z_score_se_compare_en_absolu() -> None:
    attendu = [_attendu("sensations_z", 1000.0)]
    assert comparer(attendu, _obtenu("sensations_z", 1000.0 + 0.9e-6)) == []
    assert comparer(attendu, _obtenu("sensations_z", 1000.0 + 1.1e-6)) != []


def test_une_valeur_attendue_nulle_se_compare_en_absolu() -> None:
    attendu = [_attendu("ce_courte", 0.0)]
    assert comparer(attendu, _obtenu("ce_courte", 0.0)) == []
    assert comparer(attendu, _obtenu("ce_courte", 1e-6)) != []


def test_l_etat_se_compare_en_egalite() -> None:
    attendu = [_attendu("intensite", None, "non_calculable")]
    assert comparer(attendu, _obtenu("intensite", None, "non_calculable")) == []
    assert comparer(attendu, _obtenu("intensite", None, "historique_insuffisant")) != []
    assert comparer(attendu, _obtenu("intensite", 1.0, "non_calculable")) != []


def test_valeur_manquante_ou_grandeur_non_calculee_est_un_ecart() -> None:
    assert comparer([_attendu("intensite", 1.0)], _obtenu("intensite", None)) != []
    assert comparer([_attendu("intensite", 1.0)], {}) == [
        "J1 2026-01-05 intensite : grandeur non calculée"
    ]
