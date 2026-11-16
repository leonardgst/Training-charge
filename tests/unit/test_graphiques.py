"""Spécifications Vega-Lite (Forme actuelle, charge de la fiche) : valeurs du moteur."""

import datetime

from engine.modeles import (
    CelluleSensations,
    ChargesGlissantes,
    DetailSensations,
    Etat,
    EtatForme,
    FormeActuelle,
    Parametres,
    PointForme,
)
from suivi.calculs import lire_parametres
from suivi.graphiques import (
    ETENDUE_MINIMALE,
    REPERE,
    TOTAL,
    points_barres_sensations,
    points_charges,
    points_forme,
    points_heatmap,
    specification_barres_sensations,
    specification_charges,
    specification_forme,
    specification_heatmap,
)

JOUR = datetime.date(2026, 11, 14)
PARAMETRES: Parametres = lire_parametres()


def _forme(etat: EtatForme, point: PointForme | None = None, age: int | None = None):
    return FormeActuelle(
        jour=JOUR,
        etat=etat,
        point=point,
        intensite=None,
        sensations=None,
        jour_entree=JOUR - datetime.timedelta(days=age) if age is not None else None,
        age_entree_jours=age,
        absent_depuis_jours=None,
    )


def _avec_point(i: float, s: float, c: float, age: int = 0) -> FormeActuelle:
    return _forme(EtatForme.OK, PointForme(intensite=i, sensations=s, couleur=c), age)


def _couche_points(spec: dict) -> dict:
    return spec["layer"][-1]


def test_un_point_par_joueur_qui_en_a_un_et_aucun_pour_les_autres() -> None:
    formes = [
        ("A", _avec_point(1.0, -1.0, 1.0)),
        ("B", _forme(EtatForme.ABSENT)),
        ("C", _forme(EtatForme.HISTORIQUE_INSUFFISANT)),
        ("D", _avec_point(-0.5, 0.5, -0.5, age=2)),
    ]
    points = points_forme(formes)
    assert [p["joueur"] for p in points] == ["A", "D"]
    assert points[1]["entree"] == "2026-11-12"
    assert points[1]["age"] == 2


def test_les_valeurs_du_moteur_sont_placees_telles_quelles() -> None:
    spec = specification_forme(
        [
            ("A", _avec_point(1.25, -0.75, 1.0)),
        ],
        PARAMETRES,
    )
    (point,) = _couche_points(spec)["data"]["values"]
    assert (point["intensite"], point["sensations"], point["couleur"]) == (1.25, -0.75, 1.0)


def test_l_axe_des_sensations_est_inverse_pour_mettre_les_sensations_degradees_en_haut() -> None:
    spec = specification_forme([], PARAMETRES)
    assert _couche_points(spec)["encoding"]["y"]["scale"]["reverse"] is True
    assert _couche_points(spec)["encoding"]["x"]["scale"].get("reverse") is None


def test_la_couleur_est_bornee_par_le_parametre() -> None:
    spec = specification_forme([], PARAMETRES)
    couleur = _couche_points(spec)["encoding"]["color"]["scale"]
    assert couleur["domain"] == [-PARAMETRES.couleur_borne, PARAMETRES.couleur_borne]


def test_les_reperes_sont_les_axes_en_zero_et_les_lignes_a_plus_ou_moins_deux() -> None:
    spec = specification_forme([], PARAMETRES)
    verticales, horizontales = spec["layer"][0], spec["layer"][1]
    assert sorted(r["valeur"] for r in verticales["data"]["values"]) == [-REPERE, 0, REPERE]
    assert sorted(r["valeur"] for r in horizontales["data"]["values"]) == [-REPERE, 0, REPERE]
    assert list(verticales["encoding"]) == ["x", "strokeDash"]
    assert list(horizontales["encoding"]) == ["y", "strokeDash"]


def test_les_axes_s_elargissent_pour_qu_aucun_point_ne_sorte() -> None:
    petit = specification_forme([("A", _avec_point(1.0, 1.0, 0.0))], PARAMETRES)
    grand = specification_forme([("A", _avec_point(5.2, -1.0, 3.0))], PARAMETRES)
    assert _couche_points(petit)["encoding"]["x"]["scale"]["domain"] == [
        -ETENDUE_MINIMALE,
        ETENDUE_MINIMALE,
    ]
    assert _couche_points(grand)["encoding"]["x"]["scale"]["domain"] == [-6, 6]


def test_la_date_de_l_entree_est_dans_l_infobulle() -> None:
    spec = specification_forme([("A", _avec_point(0.0, 0.0, 0.0, age=1))], PARAMETRES)
    champs = [t["field"] for t in _couche_points(spec)["encoding"]["tooltip"]]
    assert "entree" in champs


def test_les_quadrants_suivent_l_inversion_de_l_axe_des_sensations() -> None:
    spec = specification_forme([], PARAMETRES)
    quadrants = {q["texte"]: q for q in spec["layer"][2]["data"]["values"]}
    # Axe inversé : les sensations dégradées (z négatif) sont en haut, l'intensité élevée à droite.
    a_surveiller = quadrants["À surveiller"]
    assert a_surveiller["x"] > 0 and a_surveiller["y"] < 0
    assert quadrants["Récupération"]["x"] < 0 and quadrants["Récupération"]["y"] > 0


def test_les_deux_axes_portent_leur_titre_dans_chaque_couche() -> None:
    spec = specification_forme([], PARAMETRES)
    for couche in spec["layer"]:
        encodage = couche["encoding"]
        for axe in ("x", "y"):
            if axe in encodage:
                assert encodage[axe]["title"]
    titres_y = {c["encoding"]["y"]["title"] for c in spec["layer"] if "y" in c["encoding"]}
    assert titres_y == {"Sensations dégradées ↑ (z-score du joueur)"}


def _charges(n: int) -> list[ChargesGlissantes]:
    return [
        ChargesGlissantes(
            jour=JOUR + datetime.timedelta(days=i),
            ce_courte=100.0 + i,
            ce_longue=400.0 + i,
            courte_incomplete=i < 2,
            longue_incomplete=True,
        )
        for i in range(n)
    ]


def test_les_charges_du_moteur_sont_placees_telles_quelles_deux_barres_par_jour() -> None:
    points = points_charges(_charges(3))
    assert len(points) == 6
    assert [(p["grandeur"], p["valeur"]) for p in points[:2]] == [
        ("CE courte", 100.0),
        ("CE longue", 400.0),
    ]
    assert points[0]["incomplete"] is True and points[4]["incomplete"] is False
    spec = specification_charges(_charges(3))
    assert spec["data"]["values"] == points
    assert spec["encoding"]["x"]["sort"] == ["14/11", "15/11", "16/11"]


def test_sans_charge_la_specification_est_vide_mais_valide() -> None:
    spec = specification_charges([])
    assert spec["data"]["values"] == []
    assert spec["encoding"]["x"]["sort"] == []
    assert spec["mark"]["type"] == "bar"


# --- Sensations de la fiche joueur (PR 6.3) -------------------------------------------------

LIBELLES = {"plaisir": "Plaisir", "fatigue": "Fatigue"}


def _detail(
    decalage: int, plaisir: float | None, fatigue: float | None, total: float | None
) -> DetailSensations:
    jour = JOUR - datetime.timedelta(days=decalage)
    if plaisir is None and fatigue is None:
        return DetailSensations(
            jour,
            False,
            (CelluleSensations("plaisir", None, None), CelluleSensations("fatigue", None, None)),
            None,
            None,
        )
    return DetailSensations(
        jour,
        True,
        (
            CelluleSensations("plaisir", 7, plaisir),
            CelluleSensations("fatigue", None if fatigue is None else 3, fatigue),
        ),
        total,
        Etat.OK if total is not None else Etat.REPONSES_INSUFFISANTES,
    )


def test_les_barres_reprennent_les_niveaux_du_moteur_et_omettent_les_reponses_absentes() -> None:
    derniere = _detail(0, 7.0, None, None)
    points = points_barres_sensations(derniere, LIBELLES)
    assert points == [{"indicateur": "Plaisir", "niveau": 7.0, "reponse": 7}]


def test_sans_derniere_entree_les_barres_sont_vides() -> None:
    spec = specification_barres_sensations(None, LIBELLES)
    assert spec["data"]["values"] == []


def test_les_barres_sont_dans_l_ordre_des_indicateurs_sur_une_echelle_de_0_a_10() -> None:
    spec = specification_barres_sensations(_detail(0, 7.0, 8.0, 7.5), LIBELLES)
    assert spec["encoding"]["y"]["sort"] == ["Plaisir", "Fatigue"]
    assert spec["encoding"]["x"]["scale"]["domain"] == [0, 10]


def test_la_heatmap_place_les_niveaux_et_le_total_du_moteur_sans_les_recalculer() -> None:
    jours = [_detail(1, None, None, None), _detail(0, 7.0, 8.0, 7.5)]
    points = points_heatmap(jours, LIBELLES)
    assert [(p["jour"], p["indicateur"], p["niveau"]) for p in points] == [
        ("14/11", "Plaisir", 7.0),
        ("14/11", "Fatigue", 8.0),
        ("14/11", TOTAL, 7.5),
    ]
    assert not any(p["jour"] == "13/11" for p in points)


def test_sans_total_du_moteur_la_heatmap_n_en_invente_pas() -> None:
    points = points_heatmap([_detail(0, 7.0, None, None)], LIBELLES)
    assert [p["indicateur"] for p in points] == ["Plaisir"]


def test_la_heatmap_garde_les_sept_jours_en_abscisse_meme_vides() -> None:
    jours = [_detail(d, None, None, None) for d in (2, 1, 0)]
    spec = specification_heatmap(jours, LIBELLES)
    assert spec["encoding"]["x"]["sort"] == ["12/11", "13/11", "14/11"]
    assert spec["encoding"]["y"]["sort"] == ["Plaisir", "Fatigue", TOTAL]
    assert spec["data"]["values"] == []
    assert spec["encoding"]["color"]["scale"]["domain"] == [0, 10]
