"""Spécifications Vega-Lite, construites en Python (architecture, section 2).

Aucune formule ici : les valeurs viennent du moteur (`engine/forme.py`). Ce module ne fait
que les placer sur des axes. Les repères (axes en 0, lignes pointillées à ±2) sont des repères
visuels, pas un test statistique (ADR-0012, ADR-0018 Q5).
"""

import datetime
import math
from collections.abc import Sequence
from typing import Any

from engine.modeles import ChargesGlissantes, DetailSensations, FormeActuelle, Parametres
from engine.sensations import ECHELLE_AFFICHAGE

SCHEMA_VEGA_LITE = "https://vega.github.io/schema/vega-lite/v6.json"
# Repère visuel des lignes pointillées (ADR-0018, Q5).
REPERE = 2
# Demi-étendue minimale des axes, en écarts-types.
ETENDUE_MINIMALE = 4
# Libellé de la ligne de total de la heatmap.
TOTAL = "Total"


def _etendue(points: Sequence[dict[str, Any]]) -> int:
    """Demi-étendue des axes : assez grande pour qu'aucun point ne sorte du cadre."""
    plus_grand = max((max(abs(p["intensite"]), abs(p["sensations"])) for p in points), default=0.0)
    return max(ETENDUE_MINIMALE, math.ceil(plus_grand))


def points_forme(formes: Sequence[tuple[str, FormeActuelle]]) -> list[dict[str, Any]]:
    """Un enregistrement par joueur qui a un point, avec les valeurs du moteur."""
    return [
        {
            "joueur": nom,
            "intensite": forme.point.intensite,
            "sensations": forme.point.sensations,
            "couleur": forme.point.couleur,
            "entree": forme.jour_entree.isoformat() if forme.jour_entree else None,
            "age": forme.age_entree_jours,
        }
        for nom, forme in formes
        if forme.point is not None
    ]


def specification_forme(
    formes: Sequence[tuple[str, FormeActuelle]], parametres: Parametres
) -> dict[str, Any]:
    """Nuage de points « Forme actuelle » (ADR-0018) : intensité en abscisse, sensations en
    ordonnée, l'axe des sensations inversé pour que les sensations dégradées soient en haut
    (Q1), couleur du jaune au rouge selon la valeur calculée par le moteur (Q2)."""
    points = points_forme(formes)
    e = _etendue(points)
    domaine = [-e, e]
    reperes = [{"valeur": v, "style": "axe" if v == 0 else "repere"} for v in (-REPERE, 0, REPERE)]
    quadrants = [
        {"x": e - 0.15, "y": -e + 0.3, "texte": "À surveiller", "align": "right", "base": "top"},
        {
            "x": -e + 0.15,
            "y": -e + 0.3,
            "texte": "Sensations dégradées",
            "align": "left",
            "base": "top",
        },
        {
            "x": e - 0.15,
            "y": e - 0.3,
            "texte": "Intensité élevée",
            "align": "right",
            "base": "bottom",
        },
        {"x": -e + 0.15, "y": e - 0.3, "texte": "Récupération", "align": "left", "base": "bottom"},
    ]
    # Les titres sont communs à toutes les couches : Vega-Lite fusionne les axes partagés, et
    # un titre absent d'une couche l'emporterait sur celui des autres.
    x = {
        "type": "quantitative",
        "scale": {"domain": domaine},
        "title": "Intensité (z-score du joueur) →",
    }
    y = {
        "type": "quantitative",
        "scale": {"domain": domaine, "reverse": True},
        "title": "Sensations dégradées ↑ (z-score du joueur)",
    }
    return {
        "$schema": SCHEMA_VEGA_LITE,
        "description": "Intensité et sensations de chaque joueur, par rapport à lui-même",
        "width": "container",
        "height": 420,
        "autosize": {"type": "fit", "contains": "padding"},
        "layer": [
            {
                "data": {"values": reperes},
                "mark": {"type": "rule", "color": "#888", "strokeWidth": 1},
                "encoding": {
                    "x": {**x, "field": "valeur"},
                    "strokeDash": {
                        "field": "style",
                        "type": "nominal",
                        "legend": None,
                        "scale": {"domain": ["axe", "repere"], "range": [[1, 0], [4, 4]]},
                    },
                },
            },
            {
                "data": {"values": reperes},
                "mark": {"type": "rule", "color": "#888", "strokeWidth": 1},
                "encoding": {
                    "y": {**y, "field": "valeur"},
                    "strokeDash": {
                        "field": "style",
                        "type": "nominal",
                        "legend": None,
                        "scale": {"domain": ["axe", "repere"], "range": [[1, 0], [4, 4]]},
                    },
                },
            },
            {
                "data": {"values": quadrants},
                "mark": {"type": "text", "fontSize": 11, "opacity": 0.7},
                "encoding": {
                    "x": {**x, "field": "x"},
                    "y": {**y, "field": "y"},
                    "text": {"field": "texte"},
                    "align": {"field": "align", "type": "nominal", "legend": None},
                    "baseline": {"field": "base", "type": "nominal", "legend": None},
                },
            },
            {
                "data": {"values": points},
                "mark": {"type": "point", "filled": True, "size": 140, "stroke": "#333"},
                "encoding": {
                    "x": {
                        **x,
                        "field": "intensite",
                        "axis": {"tickCount": 8, "grid": False},
                    },
                    "y": {
                        **y,
                        "field": "sensations",
                        "axis": {"tickCount": 8, "grid": False},
                    },
                    "color": {
                        "field": "couleur",
                        "type": "quantitative",
                        "scale": {
                            "domain": [-parametres.couleur_borne, parametres.couleur_borne],
                            "scheme": "yelloworangered",
                        },
                        "legend": {"title": "(intensité − sensations) / 2", "orient": "bottom"},
                    },
                    "tooltip": [
                        {"field": "joueur", "title": "Joueur"},
                        {"field": "intensite", "title": "Intensité", "format": ".2f"},
                        {"field": "sensations", "title": "Sensations", "format": ".2f"},
                        {"field": "entree", "title": "Entrée du"},
                        {"field": "age", "title": "Âge de l'entrée (jours)"},
                    ],
                },
            },
        ],
    }


def points_charges(charges: Sequence[ChargesGlissantes]) -> list[dict[str, Any]]:
    """Deux enregistrements par jour (CE courte, CE longue), avec les valeurs du moteur."""
    points: list[dict[str, Any]] = []
    for c in charges:
        etiquette = c.jour.strftime("%d/%m")
        points.append(
            {
                "jour": c.jour.isoformat(),
                "etiquette": etiquette,
                "grandeur": "CE courte",
                "valeur": c.ce_courte,
                "incomplete": c.courte_incomplete,
                "fenetre": "incomplète" if c.courte_incomplete else "complète",
            }
        )
        points.append(
            {
                "jour": c.jour.isoformat(),
                "etiquette": etiquette,
                "grandeur": "CE longue",
                "valeur": c.ce_longue,
                "incomplete": c.longue_incomplete,
                "fenetre": "incomplète" if c.longue_incomplete else "complète",
            }
        )
    return points


def specification_charges(charges: Sequence[ChargesGlissantes]) -> dict[str, Any]:
    """Barres de CE courte et de CE longue, jour par jour (US-11), côte à côte pour chaque jour."""
    points = points_charges(charges)
    jours = [c.jour.strftime("%d/%m") for c in charges]
    return {
        "$schema": SCHEMA_VEGA_LITE,
        "description": "CE courte et CE longue du joueur, jour par jour",
        "width": "container",
        "height": 300,
        "autosize": {"type": "fit", "contains": "padding"},
        "data": {"values": points},
        "mark": {"type": "bar"},
        "encoding": {
            "x": {
                "field": "etiquette",
                "type": "ordinal",
                "sort": jours,
                "title": "Jour",
                "axis": {"labelAngle": -90},
            },
            "xOffset": {"field": "grandeur", "type": "nominal", "sort": ["CE courte", "CE longue"]},
            "y": {"field": "valeur", "type": "quantitative", "title": "Charge d'entraînement"},
            "color": {
                "field": "grandeur",
                "type": "nominal",
                "sort": ["CE courte", "CE longue"],
                "title": None,
                "legend": {"orient": "bottom"},
            },
            "tooltip": [
                {"field": "etiquette", "title": "Jour"},
                {"field": "grandeur", "title": "Grandeur"},
                {"field": "valeur", "title": "Valeur", "format": ".0f"},
                {"field": "fenetre", "title": "Fenêtre"},
            ],
        },
    }


def _etiquette_jour(jour: datetime.date) -> str:
    return jour.strftime("%d/%m")


def points_barres_sensations(
    derniere: DetailSensations | None, libelles: dict[str, str]
) -> list[dict[str, Any]]:
    """Un enregistrement par indicateur répondu de la dernière entrée, valeurs du moteur."""
    if derniere is None:
        return []
    return [
        {
            "indicateur": libelles[c.code],
            "niveau": c.niveau,
            "reponse": c.valeur,
        }
        for c in derniere.cellules
        if c.niveau is not None
    ]


def specification_barres_sensations(
    derniere: DetailSensations | None, libelles: dict[str, str]
) -> dict[str, Any]:
    """Barres horizontales du niveau de chaque indicateur de la dernière entrée (US-11).

    Le niveau, sur 10, est calculé par le moteur : 10 est le meilleur état, quel que soit le
    sens de l'indicateur. La réponse brute est donnée dans l'infobulle.
    """
    ordre = [libelles[c.code] for c in derniere.cellules] if derniere else []
    return {
        "$schema": SCHEMA_VEGA_LITE,
        "description": "Niveau de chaque indicateur de la dernière entrée de sensations",
        "width": "container",
        "height": {"step": 28},
        "autosize": {"type": "fit", "contains": "padding"},
        "data": {"values": points_barres_sensations(derniere, libelles)},
        "mark": {"type": "bar"},
        "encoding": {
            "y": {"field": "indicateur", "type": "nominal", "sort": ordre, "title": None},
            "x": {
                "field": "niveau",
                "type": "quantitative",
                "scale": {"domain": [0, ECHELLE_AFFICHAGE]},
                "title": "Niveau sur 10 (10 = meilleur état)",
            },
            "tooltip": [
                {"field": "indicateur", "title": "Indicateur"},
                {"field": "reponse", "title": "Réponse"},
                {"field": "niveau", "title": "Niveau sur 10", "format": ".1f"},
            ],
        },
    }


def points_heatmap(
    jours: Sequence[DetailSensations], libelles: dict[str, str]
) -> list[dict[str, Any]]:
    """Une cellule par jour et par indicateur répondu, plus le total du jour s'il existe."""
    points: list[dict[str, Any]] = []
    for j in jours:
        etiquette = _etiquette_jour(j.jour)
        for c in j.cellules:
            if c.niveau is not None:
                points.append(
                    {
                        "jour": etiquette,
                        "indicateur": libelles[c.code],
                        "niveau": c.niveau,
                        "reponse": c.valeur,
                    }
                )
        if j.total is not None:
            points.append({"jour": etiquette, "indicateur": TOTAL, "niveau": j.total})
    return points


def specification_heatmap(
    jours: Sequence[DetailSensations], libelles: dict[str, str]
) -> dict[str, Any]:
    """Heatmap des sensations sur 7 jours, par indicateur, avec une ligne de total (US-11).

    Rouge = mauvais état, jaune pâle = meilleur état, comme le rouge de « Forme actuelle ».
    Un jour ou un indicateur sans réponse reste vide.
    """
    ordre = [libelles[c.code] for c in jours[0].cellules] + [TOTAL] if jours else [TOTAL]
    return {
        "$schema": SCHEMA_VEGA_LITE,
        "description": "Sensations des 7 derniers jours, par indicateur, avec le total",
        "width": "container",
        "height": {"step": 28},
        "autosize": {"type": "fit", "contains": "padding"},
        "data": {"values": points_heatmap(jours, libelles)},
        "mark": {"type": "rect", "stroke": "#fff", "strokeWidth": 2},
        "encoding": {
            "x": {
                "field": "jour",
                "type": "ordinal",
                "sort": [_etiquette_jour(j.jour) for j in jours],
                "title": None,
                "axis": {"orient": "top", "labelAngle": 0},
            },
            "y": {"field": "indicateur", "type": "nominal", "sort": ordre, "title": None},
            "color": {
                "field": "niveau",
                "type": "quantitative",
                "scale": {
                    "domain": [0, ECHELLE_AFFICHAGE],
                    "scheme": "yelloworangered",
                    "reverse": True,
                },
                "legend": {"title": "Niveau sur 10", "orient": "bottom"},
            },
            "tooltip": [
                {"field": "jour", "title": "Jour"},
                {"field": "indicateur", "title": "Indicateur"},
                {"field": "reponse", "title": "Réponse"},
                {"field": "niveau", "title": "Niveau sur 10", "format": ".1f"},
            ],
        },
    }
