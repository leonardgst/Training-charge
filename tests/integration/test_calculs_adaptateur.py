"""Adaptateur base → moteur : séances validées seulement, jusqu'à la date de calcul (C5, C9, C10).

Cas construits dans le test, avec des valeurs calculées à la main (ADR-0007) : ils ne
remplacent pas les cas du jeu de référence.
"""

import datetime
from pathlib import Path

import pytest

from engine.modeles import ChargesGlissantes, JourCalcule, Parametres
from suivi.calculs import calculer_charges_glissantes, calculer_joueur
from tests.reference.execution import charger_en_base, executer_sans_base, executer_sur_base
from tests.reference.harnais import CasReference, lire_cas
from tests.reference.synthese import ecrire_cas

pytestmark = pytest.mark.django_db(transaction=True)

PARAMETRES = Parametres(10, 7, 28)
LUNDI = datetime.date(2026, 1, 5)
MARDI = datetime.date(2026, 1, 6)
ENTETE = "seance_id,joueur,rpe_cardio,rpe_musculaire,rpe_teta\n"


def _cas(tmp_path: Path, **fichiers: str | None) -> CasReference:
    return lire_cas(ecrire_cas(tmp_path / "C00-test", **fichiers))


def test_un_brouillon_n_entre_dans_aucun_calcul(tmp_path: Path) -> None:
    joueurs = charger_en_base(_cas(tmp_path))
    # J1 : S1 validée le 5 (3000) ; S2 brouillon le 6 ignorée, le calendrier s'arrête au 5.
    assert calculer_joueur(joueurs["J1"], MARDI, PARAMETRES) == [
        JourCalcule(LUNDI, 3000.0),
        JourCalcule(MARDI, 0.0),
    ]


def test_les_donnees_apres_la_date_de_calcul_sont_ignorees(tmp_path: Path) -> None:
    joueurs = charger_en_base(_cas(tmp_path))
    assert calculer_joueur(joueurs["J2"], LUNDI, PARAMETRES) == [JourCalcule(LUNDI, 4200.0)]
    assert calculer_joueur(joueurs["J2"], LUNDI - datetime.timedelta(days=1), PARAMETRES) == []


def test_une_seance_d_une_autre_categorie_compte_pour_le_joueur(tmp_path: Path) -> None:
    seances = "id,date,categorie,type,duree_min,statut\nS1,2026-01-05,U17,foot,60,validee\n"
    cas = _cas(
        tmp_path,
        **{
            "seances.csv": seances,
            "participations.csv": ENTETE + "S1,J1,5,6,4\n",
            "joueurs.csv": "joueur,categorie\nJ1,U19\n",
            "indicateurs.csv": None,
            "reponses.csv": None,
            "attendu.csv": None,
        },
    )
    joueurs = charger_en_base(cas)
    assert calculer_joueur(joueurs["J1"], LUNDI, PARAMETRES) == [JourCalcule(LUNDI, 3000.0)]


def test_deux_seances_le_meme_jour_sont_additionnees(tmp_path: Path) -> None:
    seances = (
        "id,date,categorie,type,duree_min,statut\n"
        "S1,2026-01-05,U19,foot,60,validee\n"
        "S2,2026-01-05,U19,musculation,45,validee\n"
    )
    cas = _cas(
        tmp_path,
        **{
            "seances.csv": seances,
            "participations.csv": ENTETE + "S1,J1,5,6,4\nS2,J1,7,7,7\n",
            "indicateurs.csv": None,
            "reponses.csv": None,
            "attendu.csv": None,
        },
    )
    joueurs = charger_en_base(cas)
    assert calculer_joueur(joueurs["J1"], LUNDI, PARAMETRES) == [JourCalcule(LUNDI, 6150.0)]


def test_les_deux_chemins_donnent_le_meme_resultat(tmp_path: Path) -> None:
    seances = "id,date,categorie,type,duree_min,statut\nS1,2026-01-05,U19,foot,60,validee\n"
    cas = _cas(
        tmp_path,
        **{
            "seances.csv": seances,
            "participations.csv": ENTETE + "S1,J1,5,6,4\nS1,J2,7,7,7\n",
            "indicateurs.csv": None,
            "reponses.csv": None,
            "attendu.csv": None,
            "cas.toml": "[parametres]\nfacteur_echelle_charge = 70\n",
        },
    )
    joueurs = charger_en_base(cas)
    jour = MARDI
    sans_base = executer_sans_base(cas, jour)
    sur_base = executer_sur_base(cas, joueurs, jour)
    assert sans_base == sur_base
    assert sans_base[("J1", LUNDI, "charge_jour")].valeur == 21000.0
    assert sans_base[("J2", MARDI, "charge_jour")].valeur == 0.0


def test_un_brouillon_est_refuse_sans_base(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="sur la base"):
        executer_sans_base(_cas(tmp_path), LUNDI)


def test_les_charges_glissantes_ignorent_brouillons_et_donnees_posterieures(tmp_path: Path) -> None:
    joueurs = charger_en_base(_cas(tmp_path))
    # J1 : S1 validée le 5 (3000), S2 brouillon le 6 ignorée ; fenêtres incomplètes.
    assert calculer_charges_glissantes(joueurs["J1"], MARDI, PARAMETRES) == [
        ChargesGlissantes(LUNDI, 3000.0, 3000.0, True, True),
        ChargesGlissantes(MARDI, 3000.0, 3000.0, True, True),
    ]
    assert calculer_charges_glissantes(joueurs["J1"], LUNDI, PARAMETRES) == [
        ChargesGlissantes(LUNDI, 3000.0, 3000.0, True, True)
    ]


def test_les_ce_sont_comparees_par_les_deux_chemins(tmp_path: Path) -> None:
    seances = "id,date,categorie,type,duree_min,statut\nS1,2026-01-05,U19,foot,60,validee\n"
    cas = _cas(
        tmp_path,
        **{
            "seances.csv": seances,
            "participations.csv": ENTETE + "S1,J1,5,6,4\nS1,J2,7,7,7\n",
            "indicateurs.csv": None,
            "reponses.csv": None,
            "attendu.csv": None,
        },
    )
    joueurs = charger_en_base(cas)
    jour = LUNDI + datetime.timedelta(days=7)
    sans_base = executer_sans_base(cas, jour)
    assert sans_base == executer_sur_base(cas, joueurs, jour)
    # Facteur 1 : J1 vaut 300 le 5. Le 12 (8e jour), la CE courte l'a perdu, la longue la garde.
    assert sans_base[("J1", jour, "ce_courte")].valeur == 0.0
    assert sans_base[("J1", jour, "ce_longue")].valeur == 300.0
    assert sans_base[("J1", LUNDI + datetime.timedelta(days=6), "ce_courte")].valeur == 300.0
