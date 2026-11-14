"""Spécification Vega-Lite de « Forme actuelle » (ADR-0018) : placement des valeurs du moteur."""

import datetime

from engine.modeles import EtatForme, FormeActuelle, Parametres, PointForme
from suivi.calculs import lire_parametres
from suivi.graphiques import ETENDUE_MINIMALE, REPERE, points_forme, specification_forme

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
