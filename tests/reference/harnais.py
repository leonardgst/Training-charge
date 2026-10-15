"""Harnais du jeu de référence : lecture, validation du format et comparaison.

Ce module ne dépend ni de Django ni du moteur : il décrit un cas (`CasReference`), le lit
depuis un dossier et compare un résultat obtenu aux valeurs attendues, avec les tolérances
de `docs/03-strategie-tests.md`, section 6. Les valeurs attendues viennent des fichiers du
mainteneur, jamais d'une sortie du code.
"""

import csv
import datetime
import tomllib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any

RACINE = Path(__file__).resolve().parent

GRANDEURS = (
    "charge_jour",
    "ce_courte",
    "ce_longue",
    "intensite",
    "score_sensations",
    "sensations_z",
)
GRANDEURS_RELATIVES = frozenset({"charge_jour", "ce_courte", "ce_longue"})
ETATS = ("ok", "historique_insuffisant", "non_calculable", "reponses_insuffisantes")
ECART_RELATIF = 1e-9
ECART_ABSOLU = 1e-6
# Un écart relatif n'a pas de sens autour de zéro : une valeur attendue nulle se compare
# avec un écart absolu.
ECART_ABSOLU_SI_ZERO = 1e-12

COLONNES = {
    "joueurs.csv": ("joueur", "categorie"),
    "seances.csv": ("id", "date", "categorie", "type", "duree_min", "statut"),
    "participations.csv": ("seance_id", "joueur", "rpe_cardio", "rpe_musculaire", "rpe_teta"),
    "indicateurs.csv": (
        "categorie",
        "code",
        "type",
        "borne_min",
        "borne_max",
        "sens",
        "poids",
        "inclus_score",
    ),
    "reponses.csv": ("joueur", "date", "indicateur", "valeur"),
    "attendu.csv": ("joueur", "date", "grandeur", "valeur", "etat"),
}


class ErreurFormat(Exception):
    """Un fichier du jeu de référence ne respecte pas le format."""


class CasAbsent(FileNotFoundError):
    """Le dossier d'un cas du registre n'existe pas encore (il est écrit par le mainteneur)."""


@dataclass(frozen=True)
class SeanceRef:
    id: str
    date: datetime.date
    categorie: str
    type: str
    duree_min: int
    statut: str


@dataclass(frozen=True)
class ParticipationRef:
    seance_id: str
    joueur: str
    rpe_cardio: int | None
    rpe_musculaire: int | None
    rpe_teta: int | None


@dataclass(frozen=True)
class IndicateurRef:
    categorie: str
    code: str
    type: str
    borne_min: int
    borne_max: int
    sens: str
    poids: Decimal
    inclus_score: bool


@dataclass(frozen=True)
class ReponseRef:
    joueur: str
    date: datetime.date
    indicateur: str
    valeur: int


@dataclass(frozen=True)
class Attendu:
    joueur: str
    date: datetime.date
    grandeur: str
    valeur: float | None
    etat: str


@dataclass(frozen=True)
class Resultat:
    valeur: float | None
    etat: str


Cle = tuple[str, datetime.date, str]


@dataclass(frozen=True)
class CasReference:
    nom: str
    description: str
    parametres: Mapping[str, object]
    joueurs: Mapping[str, str]
    seances: tuple[SeanceRef, ...]
    participations: tuple[ParticipationRef, ...]
    indicateurs: tuple[IndicateurRef, ...]
    reponses: tuple[ReponseRef, ...]
    attendu: tuple[Attendu, ...] = field(default=())

    @property
    def dates_calcul(self) -> tuple[datetime.date, ...]:
        """Chaque date d'`attendu.csv` est aussi la date de calcul : seules les données
        datées au plus tard de ce jour comptent (C9)."""
        return tuple(sorted({ligne.date for ligne in self.attendu}))


def _lire_csv(dossier: Path, nom: str) -> list[dict[str, str]]:
    chemin = dossier / nom
    if not chemin.exists():
        return []
    with chemin.open(newline="", encoding="utf-8") as fichier:
        lecteur = csv.DictReader(fichier)
        if tuple(lecteur.fieldnames or ()) != COLONNES[nom]:
            raise ErreurFormat(f"{chemin} : colonnes attendues {COLONNES[nom]}")
        return list(lecteur)


def _entier(texte: str, contexte: str) -> int:
    try:
        return int(texte)
    except ValueError:
        raise ErreurFormat(f"{contexte} : entier attendu, reçu {texte!r}") from None


def _entier_ou_vide(texte: str, contexte: str) -> int | None:
    return _entier(texte, contexte) if texte != "" else None


def _date(texte: str, contexte: str) -> datetime.date:
    try:
        return datetime.date.fromisoformat(texte)
    except ValueError:
        raise ErreurFormat(f"{contexte} : date ISO attendue, reçu {texte!r}") from None


def _booleen(texte: str, contexte: str) -> bool:
    if texte not in {"true", "false"}:
        raise ErreurFormat(f"{contexte} : `true` ou `false` attendu, reçu {texte!r}")
    return texte == "true"


def _attendu(ligne: dict[str, str], contexte: str) -> Attendu:
    if ligne["grandeur"] not in GRANDEURS:
        raise ErreurFormat(f"{contexte} : grandeur inconnue {ligne['grandeur']!r}")
    if ligne["etat"] not in ETATS:
        raise ErreurFormat(f"{contexte} : état inconnu {ligne['etat']!r}")
    if (ligne["etat"] == "ok") == (ligne["valeur"] == ""):
        raise ErreurFormat(f"{contexte} : `valeur` est renseignée si et seulement si `etat` = ok")
    try:
        valeur = float(ligne["valeur"]) if ligne["valeur"] != "" else None
    except ValueError:
        raise ErreurFormat(f"{contexte} : nombre attendu, reçu {ligne['valeur']!r}") from None
    return Attendu(
        ligne["joueur"], _date(ligne["date"], contexte), ligne["grandeur"], valeur, ligne["etat"]
    )


def lire_cas(dossier: Path, *, racine: Path | None = None) -> CasReference:
    """Lit un dossier de cas. `reprend = "<préfixe>"` dans `cas.toml` reprend les fichiers
    d'entrée d'un autre cas (C14 rejoue C06) ; les fichiers présents dans le dossier
    l'emportent, et `[parametres]` complète ceux du cas repris."""
    racine = racine or dossier.parent
    reglages = _lire_toml(dossier)
    parametres: dict[str, object] = {}
    sources = [dossier]
    reprend = reglages.get("reprend")
    if reprend is not None:
        repris = trouver_dossier(str(reprend), racine)
        parametres.update(_lire_toml(repris).get("parametres", {}))
        sources.insert(0, repris)
    parametres.update(reglages.get("parametres", {}))

    def lignes(nom: str) -> list[dict[str, str]]:
        for source in reversed(sources):
            if (source / nom).exists():
                return _lire_csv(source, nom)
        return []

    return CasReference(
        nom=dossier.name,
        description=str(reglages.get("description", "")),
        parametres=parametres,
        joueurs={ligne["joueur"]: ligne["categorie"] for ligne in lignes("joueurs.csv")},
        seances=tuple(
            SeanceRef(
                ligne["id"],
                _date(ligne["date"], f"seances.csv {ligne['id']}"),
                ligne["categorie"],
                ligne["type"],
                _entier(ligne["duree_min"], f"seances.csv {ligne['id']}"),
                ligne["statut"],
            )
            for ligne in lignes("seances.csv")
        ),
        participations=tuple(
            ParticipationRef(
                ligne["seance_id"],
                ligne["joueur"],
                *(
                    _entier_ou_vide(ligne[rpe], f"participations.csv {ligne['joueur']}")
                    for rpe in ("rpe_cardio", "rpe_musculaire", "rpe_teta")
                ),
            )
            for ligne in lignes("participations.csv")
        ),
        indicateurs=tuple(
            IndicateurRef(
                ligne["categorie"],
                ligne["code"],
                ligne["type"],
                _entier(ligne["borne_min"], f"indicateurs.csv {ligne['code']}"),
                _entier(ligne["borne_max"], f"indicateurs.csv {ligne['code']}"),
                ligne["sens"],
                Decimal(ligne["poids"]),
                _booleen(ligne["inclus_score"], f"indicateurs.csv {ligne['code']}"),
            )
            for ligne in lignes("indicateurs.csv")
        ),
        reponses=tuple(
            ReponseRef(
                ligne["joueur"],
                _date(ligne["date"], f"reponses.csv {ligne['joueur']}"),
                ligne["indicateur"],
                _entier(ligne["valeur"], f"reponses.csv {ligne['joueur']}"),
            )
            for ligne in lignes("reponses.csv")
        ),
        attendu=tuple(
            _attendu(ligne, f"attendu.csv {ligne['joueur']} {ligne['date']}")
            for ligne in lignes("attendu.csv")
        ),
    )


def _lire_toml(dossier: Path) -> dict[str, Any]:
    chemin = dossier / "cas.toml"
    if not chemin.exists():
        raise ErreurFormat(f"{chemin} : fichier absent")
    with chemin.open("rb") as fichier:
        return tomllib.load(fichier)


def trouver_dossier(prefixe: str, racine: Path = RACINE) -> Path:
    """Le dossier du cas `C06` s'appelle `C06-<description>` ; le préfixe suffit."""
    trouves = sorted(chemin for chemin in racine.glob(f"{prefixe}-*") if chemin.is_dir())
    if not trouves:
        raise CasAbsent(f"aucun dossier `{prefixe}-*` dans {racine}")
    if len(trouves) > 1:
        raise ErreurFormat(f"plusieurs dossiers `{prefixe}-*` : {[d.name for d in trouves]}")
    return trouves[0]


def verifier_coherence(cas: CasReference) -> None:
    """Contrôles croisés d'un cas lu : références entre fichiers et valeurs plausibles."""
    ids = {seance.id for seance in cas.seances}
    codes = {(i.categorie, i.code) for i in cas.indicateurs}
    for p in cas.participations:
        if p.seance_id not in ids:
            raise ErreurFormat(f"{cas.nom} : participation sur une séance inconnue {p.seance_id}")
        if p.joueur not in cas.joueurs:
            raise ErreurFormat(f"{cas.nom} : joueur inconnu {p.joueur}")
    for r in cas.reponses:
        if r.joueur not in cas.joueurs:
            raise ErreurFormat(f"{cas.nom} : joueur inconnu {r.joueur}")
        if (cas.joueurs[r.joueur], r.indicateur) not in codes:
            raise ErreurFormat(f"{cas.nom} : indicateur inconnu {r.indicateur} pour {r.joueur}")
    for a in cas.attendu:
        if a.joueur not in cas.joueurs:
            raise ErreurFormat(f"{cas.nom} : joueur inconnu {a.joueur} dans attendu.csv")
    vues: set[Cle] = set()
    for a in cas.attendu:
        cle = (a.joueur, a.date, a.grandeur)
        if cle in vues:
            raise ErreurFormat(f"{cas.nom} : ligne en double dans attendu.csv : {cle}")
        vues.add(cle)


def _proches(attendu: float, obtenu: float, grandeur: str) -> bool:
    ecart = abs(obtenu - attendu)
    if grandeur in GRANDEURS_RELATIVES:
        if attendu == 0.0:
            return ecart < ECART_ABSOLU_SI_ZERO
        return ecart < ECART_RELATIF * abs(attendu)
    return ecart < ECART_ABSOLU


def comparer(attendu: Sequence[Attendu], obtenu: Mapping[Cle, Resultat]) -> list[str]:
    """Liste des écarts entre les valeurs attendues et les résultats ; vide si tout concorde."""
    ecarts: list[str] = []
    for ligne in attendu:
        cle = (ligne.joueur, ligne.date, ligne.grandeur)
        nom = f"{ligne.joueur} {ligne.date} {ligne.grandeur}"
        resultat = obtenu.get(cle)
        if resultat is None:
            ecarts.append(f"{nom} : grandeur non calculée")
        elif resultat.etat != ligne.etat:
            ecarts.append(f"{nom} : état {resultat.etat!r} au lieu de {ligne.etat!r}")
        elif ligne.valeur is None:
            if resultat.valeur is not None:
                ecarts.append(f"{nom} : valeur {resultat.valeur!r} alors qu'aucune n'est attendue")
        elif resultat.valeur is None:
            ecarts.append(f"{nom} : valeur absente au lieu de {ligne.valeur!r}")
        elif not _proches(ligne.valeur, resultat.valeur, ligne.grandeur):
            ecarts.append(f"{nom} : {resultat.valeur!r} au lieu de {ligne.valeur!r}")
    return ecarts
