"""Spécifications Vega-Lite, construites en Python (architecture, section 2).

Aucune formule ici : les valeurs viennent du moteur (`engine/forme.py`). Ce module ne fait
que les placer sur des axes. Les repères (axes en 0, lignes pointillées à ±2) sont des repères
visuels, pas un test statistique (ADR-0012, ADR-0018 Q5).
"""

import math
from collections.abc import Sequence
from typing import Any

from engine.modeles import FormeActuelle, Parametres

SCHEMA_VEGA_LITE = "https://vega.github.io/schema/vega-lite/v6.json"
# Repère visuel des lignes pointillées (ADR-0018, Q5).
REPERE = 2
# Demi-étendue minimale des axes, en écarts-types.
ETENDUE_MINIMALE = 4


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
