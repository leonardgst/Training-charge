"""Adaptateur base → moteur : séances validées seulement, jusqu'à la date de calcul (C5, C9, C10).

Cas construits dans le test, avec des valeurs calculées à la main (ADR-0007) : ils ne
remplacent pas les cas du jeu de référence.
"""

import datetime
from pathlib import Path

import pytest

from engine.modeles import ChargesGlissantes, Etat, JourCalcule, Parametres
from suivi.calculs import (
    calculer_charges_glissantes,
    calculer_intensite,
    calculer_joueur,
    calculer_sensations,
    charges_de_seance,
)
from suivi.models import Categorie, Joueur, Participation, Seance
from tests.reference.execution import charger_en_base, executer_sans_base, executer_sur_base
from tests.reference.harnais import CasReference, lire_cas
from tests.reference.synthese import ecrire_cas

pytestmark = pytest.mark.django_db(transaction=True)

PARAMETRES = Parametres(10, 7, 28, 28, 21, 1e-9, 0.5, 28, 6)
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


def test_l_intensite_d_un_historique_court_est_insuffisante_et_les_deux_chemins_concordent(
    tmp_path: Path,
) -> None:
    seances = "id,date,categorie,type,duree_min,statut\nS1,2026-01-05,U19,foot,60,validee\n"
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
    jour = LUNDI + datetime.timedelta(days=40)
    z = calculer_intensite(joueurs["J1"], jour, PARAMETRES)
    assert len(z) == 41
    # Une seule séance suivie de jours à 0 : la référence est constante ou trop courte.
    assert all(r.etat in Etat for r in z)
    assert executer_sans_base(cas, jour) == executer_sur_base(cas, joueurs, jour)
    assert executer_sur_base(cas, joueurs, jour)[("J1", LUNDI, "intensite")].etat == (
        "historique_insuffisant"
    )


SEANCE_VALIDEE = "id,date,categorie,type,duree_min,statut\nS1,2026-01-05,U19,foot,60,validee\n"
INDICATEURS = (
    "categorie,code,type,borne_min,borne_max,sens,poids,inclus_score\n"
    "U19,plaisir,note,0,10,haut_bon,1,true\n"
    "U19,fatigue,note,0,10,bas_bon,1,true\n"
    "U19,heure_coucher,heure,0,1439,aucun,1,false\n"
)


def _cas_sensations(tmp_path: Path, indicateurs: str, reponses: str) -> CasReference:
    return _cas(
        tmp_path,
        **{
            "indicateurs.csv": indicateurs,
            "reponses.csv": "joueur,date,indicateur,valeur\n" + reponses,
            "attendu.csv": None,
        },
    )


def test_le_score_d_une_entree_ignore_les_indicateurs_hors_score(tmp_path: Path) -> None:
    reponses = (
        "J1,2026-01-05,plaisir,8\nJ1,2026-01-05,fatigue,2\nJ1,2026-01-05,heure_coucher,1380\n"
    )
    joueurs = charger_en_base(_cas_sensations(tmp_path, INDICATEURS, reponses))
    scores, z = calculer_sensations(joueurs["J1"], LUNDI, PARAMETRES)
    assert [(s.jour, s.valeur, s.etat) for s in scores] == [(LUNDI, pytest.approx(0.8), Etat.OK)]
    assert z[0].etat is Etat.HISTORIQUE_INSUFFISANT


def test_les_entrees_apres_la_date_de_calcul_sont_ignorees(tmp_path: Path) -> None:
    reponses = "J1,2026-01-05,plaisir,8\nJ1,2026-01-05,fatigue,2\nJ1,2026-01-06,plaisir,0\n"
    joueurs = charger_en_base(_cas_sensations(tmp_path, INDICATEURS, reponses))
    scores, _ = calculer_sensations(joueurs["J1"], LUNDI, PARAMETRES)
    assert [s.jour for s in scores] == [LUNDI]
    assert [s.jour for s in calculer_sensations(joueurs["J1"], MARDI, PARAMETRES)[0]] == [
        LUNDI,
        MARDI,
    ]


def test_c15_un_changement_de_poids_est_retroactif(tmp_path: Path) -> None:
    from suivi.models import Indicateur

    reponses = "J1,2026-01-05,plaisir,10\nJ1,2026-01-05,fatigue,10\n"
    joueurs = charger_en_base(_cas_sensations(tmp_path, INDICATEURS, reponses))
    avant, _ = calculer_sensations(joueurs["J1"], LUNDI, PARAMETRES)
    assert avant[0].valeur == pytest.approx(0.5)  # (1 + 0) / 2
    Indicateur.objects.filter(code="plaisir").update(poids=3)
    apres, _ = calculer_sensations(joueurs["J1"], LUNDI, PARAMETRES)
    assert apres[0].valeur == pytest.approx(0.75)  # (3 × 1 + 0) / 4


def test_c15_un_indicateur_ajoute_n_entre_que_dans_les_entrees_qui_y_repondent(
    tmp_path: Path,
) -> None:
    from suivi.models import EntreeSensations, Indicateur, Reponse

    reponses = "J1,2026-01-05,plaisir,10\nJ1,2026-01-05,fatigue,0\n"
    joueurs = charger_en_base(_cas_sensations(tmp_path, INDICATEURS, reponses))
    categorie = Indicateur.objects.get(code="plaisir").categorie
    energie = Indicateur.objects.create(
        categorie=categorie, code="energie", libelle="Énergie", type="note",
        borne_min=0, borne_max=10, sens="haut_bon", poids=1, inclus_score=True,
    )  # fmt: skip
    entree = EntreeSensations.objects.create(joueur_id=joueurs["J1"], date=MARDI)
    for indicateur in ("plaisir", "fatigue"):
        Reponse.objects.create(
            entree=entree, indicateur=Indicateur.objects.get(code=indicateur), valeur=5
        )
    Reponse.objects.create(entree=entree, indicateur=energie, valeur=10)
    scores, _ = calculer_sensations(joueurs["J1"], MARDI, PARAMETRES)
    # Le 5 : 2 indicateurs répondus sur 3 (67 %), score (1 + 1) / 2 = 1.
    # Le 6 : (0,5 + 0,5 + 1) / 3.
    assert [s.valeur for s in scores] == [pytest.approx(1.0), pytest.approx(2 / 3)]


def test_un_indicateur_desactive_sort_du_score_sans_perdre_ses_reponses(tmp_path: Path) -> None:
    from suivi.models import Indicateur, Reponse

    reponses = "J1,2026-01-05,plaisir,10\nJ1,2026-01-05,fatigue,10\n"
    joueurs = charger_en_base(_cas_sensations(tmp_path, INDICATEURS, reponses))
    Indicateur.objects.filter(code="fatigue").update(actif=False)
    scores, _ = calculer_sensations(joueurs["J1"], LUNDI, PARAMETRES)
    assert scores[0].valeur == pytest.approx(1.0)
    assert Reponse.objects.filter(indicateur__code="fatigue").count() == 1


def test_les_deux_chemins_donnent_les_memes_sensations(tmp_path: Path) -> None:
    reponses = "".join(
        f"J1,2026-01-{5 + i:02d},{code},{(i * 3 + k) % 11}\n"
        for i in range(10)
        for k, code in enumerate(("plaisir", "fatigue"))
    )
    cas = _cas(
        tmp_path,
        **{
            "seances.csv": SEANCE_VALIDEE,
            "participations.csv": ENTETE + "S1,J1,5,6,4\n",
            "indicateurs.csv": INDICATEURS,
            "reponses.csv": "joueur,date,indicateur,valeur\n" + reponses,
            "attendu.csv": None,
        },
    )
    joueurs = charger_en_base(cas)
    jour = LUNDI + datetime.timedelta(days=9)
    sur_base = executer_sur_base(cas, joueurs, jour)
    assert executer_sans_base(cas, jour) == sur_base
    assert sur_base[("J1", jour, "score_sensations")].etat == "ok"
    assert sur_base[("J1", jour, "sensations_z")].etat == "ok"
    assert sur_base[("J1", LUNDI, "sensations_z")].etat == "historique_insuffisant"
    assert ("J2", LUNDI, "score_sensations") not in sur_base


# --- Charges d'une séance, pour sa page (PR 4.4) ----------------------------------------


def _seance_avec(statut: str, *rpe: tuple[int | None, int | None, int | None]) -> Seance:
    u19 = Categorie.objects.create(code="U19", libelle="U19")
    seance = Seance.objects.create(
        categorie_organisatrice=u19, date=LUNDI, type="foot", duree_min=90
    )
    for numero, (cardio, musculaire, teta) in enumerate(rpe):
        joueur = Joueur.objects.create(
            nom=f"J{numero}",
            prenom="Test",
            date_naissance=datetime.date(2007, 3, 14),
            categorie_reference=u19,
        )
        Participation.objects.create(
            seance=seance,
            joueur=joueur,
            rpe_cardio=cardio,
            rpe_musculaire=musculaire,
            rpe_teta=teta,
        )
    if statut == "validee":
        seance.statut = "validee"
        seance.validated_at = datetime.datetime(2026, 1, 5, 20, 0, tzinfo=datetime.UTC)
        seance.save()
    return seance


def test_charges_d_une_seance_validee_calculees_a_la_main() -> None:
    seance = _seance_avec("validee", (5, 6, 4), (7, 7, 7), (0, 0, 0))
    participations = list(seance.participations.order_by("joueur__nom"))

    charges = charges_de_seance(seance, participations, PARAMETRES)

    # (5 + 6 + 4) / 3 × 90 × 10 = 4500 ; 7 × 90 × 10 = 6300 ; 0.
    assert charges == {
        participations[0].pk: pytest.approx(4500.0, rel=1e-9),
        participations[1].pk: pytest.approx(6300.0, rel=1e-9),
        participations[2].pk: pytest.approx(0.0, abs=1e-12),
    }


def test_une_seance_en_brouillon_n_a_aucune_charge() -> None:
    seance = _seance_avec("brouillon", (5, 6, 4), (None, 2, None))

    assert charges_de_seance(seance, seance.participations.all(), PARAMETRES) == {}


def test_une_participation_d_une_autre_seance_est_refusee() -> None:
    seance = _seance_avec("validee", (5, 6, 4))
    autre = Seance.objects.create(
        categorie_organisatrice=seance.categorie_organisatrice,
        date=LUNDI,
        type="yoga",
        duree_min=30,
    )
    intruse = Participation(seance=autre, joueur=Joueur.objects.get(), rpe_cardio=1)

    with pytest.raises(ValueError, match="n'appartient pas"):
        charges_de_seance(seance, [intruse], PARAMETRES)


def test_une_participation_incomplete_d_une_seance_validee_est_une_anomalie() -> None:
    seance = _seance_avec("validee", (5, 6, 4))
    # Le déclencheur l'interdit en base : objet construit en mémoire seulement.
    incomplete = Participation(seance=seance, joueur=Joueur.objects.get(), rpe_cardio=5)

    with pytest.raises(ValueError, match="incomplète"):
        charges_de_seance(seance, [incomplete], PARAMETRES)
