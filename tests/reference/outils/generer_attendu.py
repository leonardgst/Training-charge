"""Calcul indépendant des valeurs attendues du jeu de référence.

Ce script n'importe ni `engine` ni `suivi` : il relit les fichiers d'entrée d'un cas et
refait les calculs depuis les ADR, en arithmétique exacte (`Fraction`), la seule racine
carrée étant prise en décimal à 40 chiffres. Il écrit un `attendu.csv` par cas dans le
dossier donné en argument.

    python generer_attendu.py <dossier de sortie> [C06 C07 ...]

Formules (ADR-0007, 0011, 0012, 0014, 0015) :

- charge d'une participation = (cardio + musculaire + TETA) / 3 × durée × facteur ;
- charge du jour = somme sur les séances validées du jour ; calendrier continu de la
  première participation validée à la date de calcul D ;
- CE courte (CE longue) = somme des charges des 7 (28) derniers jours du calendrier ;
  la fenêtre est complète quand le calendrier compte au moins 7 (28) jours ;
- intensité = (CE courte(D) − m) / s sur les CE courtes à fenêtre complète de D − 28 à
  D − 1 (au moins 21 jours), s écart-type d'échantillon ; s ≤ 1e-9 × max(1, |m|) →
  non calculable ;
- score d'une entrée = Σ(poids × u) / Σ(poids), u = (v − min) / (max − min), inversé si
  bas = bon, sur les indicateurs notés et inclus ; au moins 50 % du poids total ;
- sensations (z) = z-score du score contre les scores des entrées de D − 28 à D − 1
  (au moins 6), même estimateur.
"""

import csv
import datetime as dt
import sys
import tomllib
from decimal import Decimal, getcontext
from fractions import Fraction
from pathlib import Path

getcontext().prec = 40
RACINE = Path(__file__).resolve().parent.parent
CONFIG = RACINE.parent.parent / "config" / "calcul.toml"
TOLERANCE_ECART_TYPE = Fraction("1e-9")
JOUR = dt.timedelta(days=1)


def d(texte: str) -> dt.date:
    return dt.date.fromisoformat(texte)


def lire(dossier: Path, nom: str) -> list[dict[str, str]]:
    chemin = dossier / nom
    if not chemin.exists():
        return []
    with chemin.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def toml(dossier: Path) -> dict:
    with (dossier / "cas.toml").open("rb") as f:
        return tomllib.load(f)


def racine_carree(x: Fraction) -> Fraction:
    if x == 0:
        return Fraction(0)
    racine = (Decimal(x.numerator) / Decimal(x.denominator)).sqrt()
    return Fraction(racine)


def ecart_type(valeurs: list[Fraction]) -> tuple[Fraction, Fraction]:
    """Moyenne et écart-type d'échantillon (n − 1)."""
    n = len(valeurs)
    m = sum(valeurs, Fraction(0)) / n
    variance = sum(((v - m) ** 2 for v in valeurs), Fraction(0)) / (n - 1)
    return m, racine_carree(variance)


def zscore(
    valeur: Fraction, reference: list[Fraction], minimum: int
) -> tuple[Fraction | None, str]:
    if len(reference) < minimum:
        return None, "historique_insuffisant"
    m, s = ecart_type(reference)
    if s <= TOLERANCE_ECART_TYPE * max(Fraction(1), abs(m)):
        return None, "non_calculable"
    return (valeur - m) / s, "ok"


class Cas:
    def __init__(self, dossier: Path):
        self.dossier = dossier
        reglages = toml(dossier)
        sources = [dossier]
        self.parametres: dict = {}
        if "reprend" in reglages:
            repris = next(RACINE.glob(f"{reglages['reprend']}-*"))
            sources.insert(0, repris)
            self.parametres.update(toml(repris).get("parametres", {}))
        self.parametres.update(reglages.get("parametres", {}))
        with CONFIG.open("rb") as f:
            self.facteur = Fraction(str(tomllib.load(f)["facteur_echelle_charge"]))
        if "facteur_echelle_charge" in self.parametres:
            self.facteur = Fraction(str(self.parametres["facteur_echelle_charge"]))

        def fichier(nom: str) -> list[dict[str, str]]:
            for source in reversed(sources):
                if (source / nom).exists():
                    return lire(source, nom)
            return []

        self.joueurs = {r["joueur"]: r["categorie"] for r in fichier("joueurs.csv")}
        self.seances = {r["id"]: r for r in fichier("seances.csv")}
        self.participations = fichier("participations.csv")
        self.indicateurs = fichier("indicateurs.csv")
        self.reponses = fichier("reponses.csv")

    # ---- charge ------------------------------------------------------------------------
    def charges_du_jour(self, joueur: str, fin: dt.date) -> dict[dt.date, Fraction]:
        par_jour: dict[dt.date, Fraction] = {}
        for p in self.participations:
            if p["joueur"] != joueur:
                continue
            s = self.seances[p["seance_id"]]
            jour = d(s["date"])
            if s["statut"] != "validee" or jour > fin:
                continue
            rpe = sum(int(p[c]) for c in ("rpe_cardio", "rpe_musculaire", "rpe_teta"))
            charge = Fraction(rpe, 3) * int(s["duree_min"]) * self.facteur
            par_jour[jour] = par_jour.get(jour, Fraction(0)) + charge
        return par_jour

    def calendrier(self, joueur: str, fin: dt.date) -> list[tuple[dt.date, Fraction]]:
        par_jour = self.charges_du_jour(joueur, fin)
        if not par_jour:
            return []
        debut = min(par_jour)
        n = (fin - debut).days + 1
        return [(debut + i * JOUR, par_jour.get(debut + i * JOUR, Fraction(0))) for i in range(n)]

    def ce(self, calendrier: list[tuple[dt.date, Fraction]], i: int, fenetre: int) -> Fraction:
        return sum((c for _, c in calendrier[max(0, i - fenetre + 1) : i + 1]), Fraction(0))

    def intensite(self, joueur: str, fin: dt.date) -> tuple[Fraction | None, str]:
        cal = self.calendrier(joueur, fin)
        i = len(cal) - 1
        reference = [
            self.ce(cal, k, 7)
            for k in range(max(0, i - 28), i)
            if k + 1 >= 7  # fenêtre courte complète
        ]
        return zscore(self.ce(cal, i, 7), reference, 21)

    # ---- sensations --------------------------------------------------------------------
    def scores(self, joueur: str, fin: dt.date) -> dict[dt.date, Fraction | None]:
        categorie = self.joueurs[joueur]
        inclus = {
            r["code"]: r
            for r in self.indicateurs
            if r["categorie"] == categorie and r["inclus_score"] == "true" and r["type"] == "note"
        }
        total = sum((Fraction(r["poids"]) for r in inclus.values()), Fraction(0))
        entrees: dict[dt.date, dict[str, int]] = {}
        for r in self.reponses:
            if r["joueur"] == joueur and d(r["date"]) <= fin:
                entrees.setdefault(d(r["date"]), {})[r["indicateur"]] = int(r["valeur"])
        resultat: dict[dt.date, Fraction | None] = {}
        for jour, reponses in entrees.items():
            somme = repondu = Fraction(0)
            for code, ind in inclus.items():
                if code not in reponses:
                    continue
                mini, maxi = int(ind["borne_min"]), int(ind["borne_max"])
                u = Fraction(reponses[code] - mini, maxi - mini)
                if ind["sens"] == "bas_bon":
                    u = 1 - u
                poids = Fraction(ind["poids"])
                somme += poids * u
                repondu += poids
            resultat[jour] = somme / repondu if repondu * 2 >= total and repondu > 0 else None
        return resultat

    def sensations(self, joueur: str, jour: dt.date) -> tuple[Fraction | None, str]:
        scores = self.scores(joueur, jour)
        courant = scores[jour]
        if courant is None:
            return None, "reponses_insuffisantes"
        reference = [
            v for j, v in scores.items() if v is not None and jour - 28 * JOUR <= j <= jour - JOUR
        ]
        return zscore(courant, reference, 6)


def nombre(x: Fraction | None) -> str:
    if x is None:
        return ""
    if x == 0:
        return "0"
    # 15 chiffres significatifs, bien au-delà des 10 exigés.
    return format(Decimal(x.numerator) / Decimal(x.denominator), ".15g")


def dates(debut: str, fin: str) -> list[str]:
    a, b = d(debut), d(fin)
    return [(a + i * JOUR).isoformat() for i in range((b - a).days + 1)]


CHARGES = ("charge_jour", "ce_courte", "ce_longue")
INTENSITE = ("intensite",)
SENSATIONS = ("score_sensations", "sensations_z")

# Cas -> liste de (joueurs, dates, grandeurs). Les dates sont celles de la `description`
# de chaque `cas.toml`.
PLAN: dict[str, list[tuple[tuple[str, ...], list[str], tuple[str, ...]]]] = {
    "C01": [(("J1",), ["2026-01-05"], CHARGES + INTENSITE)],
    "C02": [(("J1", "J2"), ["2026-01-05"], CHARGES)],
    "C03": [(("J1",), dates("2026-01-05", "2026-01-16"), CHARGES)],
    "C04": [(("J1",), dates("2026-02-06", "2026-02-16"), CHARGES + INTENSITE)],
    "C05": [(("J1",), dates("2026-01-05", "2026-01-07"), CHARGES)],
    "C06": [(("J1",), ["2026-02-01", "2026-02-08", "2026-02-09"], CHARGES + INTENSITE)],
    "C07": [
        (("J1",), ["2026-02-01", "2026-02-13"], CHARGES + INTENSITE),
        (("J1",), ["2026-01-14"], SENSATIONS),
    ],
    "C08": [
        (("J1",), ["2026-01-13"], INTENSITE),
        (("J2",), ["2026-01-31", "2026-02-01"], INTENSITE),
        (("J2",), ["2026-01-15", "2026-01-17"], SENSATIONS),
    ],
    "C09": [(("J1",), ["2026-02-05"], CHARGES + INTENSITE + SENSATIONS)],
    "C10": [(("J1", "J2"), ["2026-01-05", "2026-01-06"], CHARGES)],
    "C11": [(("J1",), ["2026-01-05"], SENSATIONS)],
    "C12": [(("J1",), dates("2026-01-05", "2026-01-07"), SENSATIONS)],
    "C13": [(("J1",), dates("2026-01-05", "2026-01-09"), ("score_sensations",))],
    "C14": [(("J1",), ["2026-02-01", "2026-02-08", "2026-02-09"], CHARGES + INTENSITE)],
    "C15": [(("J1",), ["2026-01-09", "2026-01-10", "2026-01-11", "2026-01-14"], SENSATIONS)],
}


def valeur(cas: Cas, joueur: str, jour: str, grandeur: str) -> tuple[Fraction | None, str]:
    fin = d(jour)
    if grandeur in CHARGES:
        cal = cas.calendrier(joueur, fin)
        i = len(cal) - 1
        if grandeur == "charge_jour":
            return cal[i][1], "ok"
        return cas.ce(cal, i, 7 if grandeur == "ce_courte" else 28), "ok"
    if grandeur == "intensite":
        return cas.intensite(joueur, fin)
    if grandeur == "score_sensations":
        score = cas.scores(joueur, fin)[fin]
        return (score, "ok") if score is not None else (None, "reponses_insuffisantes")
    return cas.sensations(joueur, fin)


def main() -> None:
    sortie = Path(sys.argv[1])
    voulus = sys.argv[2:] or sorted(PLAN)
    for numero in voulus:
        dossier = next(RACINE.glob(f"{numero}-*"))
        cas = Cas(dossier)
        lignes: list[tuple[str, str, str, str, str]] = []
        for joueurs, jours, grandeurs in PLAN[numero]:
            for joueur in joueurs:
                for jour in jours:
                    for grandeur in grandeurs:
                        v, etat = valeur(cas, joueur, jour, grandeur)
                        lignes.append((joueur, jour, grandeur, nombre(v), etat))
        cible = sortie / dossier.name
        cible.mkdir(parents=True, exist_ok=True)
        with (cible / "attendu.csv").open("w", newline="", encoding="utf-8") as f:
            ecrivain = csv.writer(f, lineterminator="\n")
            ecrivain.writerow(("joueur", "date", "grandeur", "valeur", "etat"))
            ecrivain.writerows(sorted(lignes))


if __name__ == "__main__":
    main()
