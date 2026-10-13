"""Données de démonstration, fictives et reproductibles (F13).

Graine fixe : deux exécutions avec la même date de fin produisent les mêmes joueurs, les
mêmes séances et les mêmes saisies. Aucune donnée réelle : les noms sont tirés de deux
listes de prénoms et de noms courants, assemblés au hasard.

La commande refuse de s'exécuter sur une base qui contient déjà des données. Pour repartir
de zéro en local : `docker compose down -v && docker compose up -d db`.
"""

import datetime
import random
import secrets
from argparse import ArgumentParser
from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from suivi.horloge import FUSEAU, aujourd_hui
from suivi.models import (
    Categorie,
    EntreeSensations,
    Indicateur,
    Joueur,
    Participation,
    Preparateur,
    Reponse,
    Seance,
)

GRAINE = 20261012
JOURS_HISTORIQUE = 56  # huit semaines : de quoi remplir la fenêtre longue de 28 jours

PRENOMS = [
    "Lucas", "Hugo", "Nathan", "Louis", "Ethan", "Jules", "Adam", "Noah", "Tom", "Enzo",
    "Mathis", "Maxime", "Théo", "Léo", "Gabin", "Rayan", "Axel", "Yanis", "Malo", "Evan",
    "Paul", "Sacha", "Nolan", "Timéo", "Baptiste", "Clément", "Antoine", "Kylian", "Samy", "Eliott",
]  # fmt: skip
NOMS = [
    "Martin", "Bernard", "Dubois", "Thomas", "Robert", "Richard", "Petit", "Durand", "Leroy",
    "Moreau", "Simon", "Laurent", "Lefebvre", "Michel", "Garcia", "David", "Bertrand", "Roux",
    "Vincent", "Fournier", "Morel", "Girard", "André", "Mercier", "Dupont", "Lambert",
    "Bonnet", "François", "Martinez", "Legrand", "Garnier", "Faure", "Rousseau", "Blanc",
]  # fmt: skip

# (code, libellé, type, borne_min, borne_max, sens, poids, inclus_score) — ADR-0010
NOTES_U19 = [
    ("concentration", "Concentration", "haut_bon"),
    ("plaisir", "Plaisir", "haut_bon"),
    ("fatigue", "Fatigue", "bas_bon"),
    ("energie", "Énergie", "haut_bon"),
    ("sommeil", "Qualité du sommeil", "haut_bon"),
    ("douleurs", "Douleurs musculaires", "bas_bon"),
    ("comprehension", "Compréhension des consignes", "haut_bon"),
]
NOTES_U17 = [NOTES_U19[0], NOTES_U19[1], NOTES_U19[2]]

# jour de semaine (0 = lundi) -> (type, durée en minutes, intensité de base)
PLAN_U19: dict[int, tuple[str, int, float]] = {
    0: ("musculation", 60, 6.0),
    1: ("foot", 90, 6.5),
    2: ("foot", 75, 6.0),
    3: ("foot", 90, 7.0),
    4: ("yoga", 45, 3.0),
    5: ("foot", 100, 7.5),
}
PLAN_U17: dict[int, tuple[str, int, float]] = {
    0: ("foot", 75, 6.0),
    2: ("foot", 75, 6.5),
    4: ("foot", 60, 5.5),
}
JOURS_INVITES = {1, 3, 5}  # jours où les U17 invités s'entraînent avec les U19

JOUEURS_U19 = 24
JOUEURS_U17 = 8
INVITES = 3
JOURS_A_SURVEILLER = 10


def _borner(valeur: float, bas: int, haut: int) -> int:
    return max(bas, min(haut, round(valeur)))


class Command(BaseCommand):
    help = "Charge les données de démonstration (deux catégories, joueurs fictifs, huit semaines)."

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--fin",
            type=datetime.date.fromisoformat,
            default=None,
            help="dernier jour des données, AAAA-MM-JJ (défaut : aujourd'hui, heure de Paris)",
        )
        parser.add_argument(
            "--mot-de-passe",
            default=None,
            help="mot de passe des trois comptes de démonstration (défaut : tiré au hasard)",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        if Categorie.objects.exists() or Joueur.objects.exists():
            raise CommandError("la base contient déjà des données : rien n'a été chargé")
        fin: datetime.date = options["fin"] or aujourd_hui()
        mot_de_passe: str = options["mot_de_passe"] or secrets.token_urlsafe(12)

        with transaction.atomic():
            # Graine fixe voulue : données fictives reproductibles, aucun secret.
            rng = random.Random(GRAINE)  # noqa: S311
            effectifs = _Generateur(rng, fin, mot_de_passe).generer()

        self.stdout.write(self.style.SUCCESS("Démonstration chargée :"))
        for nom, valeur in effectifs.items():
            self.stdout.write(f"  {nom} : {valeur}")
        self.stdout.write("Comptes : admin_demo, prep_u19, prep_u17")
        if not options["mot_de_passe"]:
            self.stdout.write(f"Mot de passe (affiché une seule fois) : {mot_de_passe}")


class _Generateur:
    def __init__(self, rng: random.Random, fin: datetime.date, mot_de_passe: str) -> None:
        self.rng = rng
        self.fin = fin
        self.debut = fin - datetime.timedelta(days=JOURS_HISTORIQUE - 1)
        self.mot_de_passe = mot_de_passe
        # moyenne des RPE de la veille, par joueur : couple la fatigue à la charge
        self.derniere_charge: dict[int, float] = {}
        self.a_surveiller: int | None = None

    def generer(self) -> dict[str, int]:
        utilisateurs = get_user_model().objects
        utilisateurs.create_superuser("admin_demo", password=self.mot_de_passe)
        u19 = Categorie.objects.create(code="U19", libelle="Moins de 19 ans")
        u17 = Categorie.objects.create(
            code="U17", libelle="Moins de 17 ans", jours_questionnaire=[0, 1, 2, 3, 4]
        )
        comptes = {}
        for categorie in (u19, u17):
            compte = utilisateurs.create_user(
                f"prep_{categorie.code.lower()}", password=self.mot_de_passe
            )
            Preparateur.objects.create(user=compte, categorie=categorie)
            comptes[categorie.code] = compte

        indicateurs = {
            u19.code: self._indicateurs(u19, NOTES_U19, avec_heures=True),
            u17.code: self._indicateurs(u17, NOTES_U17, avec_heures=False),
        }
        noms = self._noms_uniques(JOUEURS_U19 + 1 + JOUEURS_U17)
        joueurs_u19 = [self._joueur(noms.pop(), u19) for _ in range(JOUEURS_U19)]
        archive = self._joueur(noms.pop(), u19, actif=False)
        joueurs_u17 = [self._joueur(noms.pop(), u17) for _ in range(JOUEURS_U17)]
        invites = joueurs_u17[:INVITES]
        self.a_surveiller = joueurs_u19[0].pk

        # Le joueur archivé a quitté le groupe au milieu de la période.
        depart = self.debut + datetime.timedelta(days=JOURS_HISTORIQUE // 2)
        nb_seances = 0
        nb_participations = 0
        dernier_u19: Seance | None = None
        for jour in self._jours():
            plan = PLAN_U19.get(jour.weekday())
            if plan:
                presents = list(joueurs_u19)
                if jour <= depart:
                    presents.append(archive)
                presents += [j for j in invites if self.rng.random() < 0.5]
                dernier_u19, n = self._seance(u19, comptes["U19"], jour, plan, presents)
                nb_seances += 1
                nb_participations += n
            plan17 = PLAN_U17.get(jour.weekday())
            if plan17:
                _, n = self._seance(u17, comptes["U17"], jour, plan17, joueurs_u17)
                nb_seances += 1
                nb_participations += n
        if dernier_u19 is None:
            raise CommandError("aucune séance U19 sur la période")
        self._laisser_en_brouillon(dernier_u19)

        nb_entrees = 0
        nb_reponses = 0
        for categorie, joueurs in ((u19, [*joueurs_u19, archive]), (u17, joueurs_u17)):
            e, r = self._sensations(
                categorie, joueurs, indicateurs[categorie.code], depart, archive
            )
            nb_entrees += e
            nb_reponses += r

        return {
            "catégories": 2,
            "comptes": 3,
            "joueurs (dont 1 archivé)": JOUEURS_U19 + 1 + JOUEURS_U17,
            "séances": nb_seances,
            "participations": nb_participations,
            "entrées de sensations": nb_entrees,
            "réponses": nb_reponses,
        }

    # --- référentiel -----------------------------------------------------------------

    def _indicateurs(
        self, categorie: Categorie, notes: list[tuple[str, str, str]], avec_heures: bool
    ) -> list[Indicateur]:
        liste = [
            Indicateur(
                categorie=categorie,
                code=code,
                libelle=libelle,
                type="note",
                borne_min=0,
                borne_max=10,
                sens=sens,
                ordre=ordre,
            )
            for ordre, (code, libelle, sens) in enumerate(notes)
        ]
        if avec_heures:
            for code, libelle in (
                ("heure_coucher", "Heure de coucher"),
                ("heure_lever", "Heure de lever"),
            ):
                liste.append(
                    Indicateur(
                        categorie=categorie,
                        code=code,
                        libelle=libelle,
                        type="heure",
                        borne_min=0,
                        borne_max=1439,
                        sens="aucun",
                        poids=0,
                        inclus_score=False,
                        ordre=len(liste),
                    )
                )
        return Indicateur.objects.bulk_create(liste)

    def _noms_uniques(self, n: int) -> list[tuple[str, str]]:
        couples = [(p, nom) for p in PRENOMS for nom in NOMS]
        return self.rng.sample(couples, n)

    def _joueur(
        self, nom_complet: tuple[str, str], categorie: Categorie, actif: bool = True
    ) -> Joueur:
        prenom, nom = nom_complet
        annee = 2007 if categorie.code == "U19" else 2009
        naissance = datetime.date(annee, 1, 1) + datetime.timedelta(days=self.rng.randrange(365))
        return Joueur.objects.create(
            nom=nom,
            prenom=prenom,
            date_naissance=naissance,
            categorie_reference=categorie,
            actif=actif,
        )

    def _jours(self) -> list[datetime.date]:
        return [self.debut + datetime.timedelta(days=i) for i in range(JOURS_HISTORIQUE)]

    # --- séances -----------------------------------------------------------------------

    def _seance(
        self,
        categorie: Categorie,
        compte: Any,
        jour: datetime.date,
        plan: tuple[str, int, float],
        joueurs: list[Joueur],
    ) -> tuple[Seance, int]:
        type_seance, duree, intensite = plan
        seance = Seance.objects.create(
            categorie_organisatrice=categorie,
            date=jour,
            type=type_seance,
            duree_min=duree,
            created_by=compte,
        )
        en_derive = (self.fin - jour).days < JOURS_A_SURVEILLER
        participations = []
        for joueur in joueurs:
            if self.rng.random() > 0.92:
                continue  # absent
            surcharge = 2.0 if en_derive and joueur.pk == self.a_surveiller else 0.0
            base = intensite + surcharge + self.rng.gauss(0, 0.6)
            rpe = [
                _borner(base + self.rng.gauss(0, 0.9), 0, 10),
                _borner(
                    base + (1 if type_seance == "musculation" else 0) + self.rng.gauss(0, 0.9),
                    0,
                    10,
                ),
                _borner(
                    base
                    - (3 if type_seance in {"musculation", "yoga"} else 0)
                    + self.rng.gauss(0, 0.9),
                    0,
                    10,
                ),
            ]
            self.derniere_charge[joueur.pk] = sum(rpe) / 3
            participations.append(
                Participation(
                    seance=seance,
                    joueur=joueur,
                    rpe_cardio=rpe[0],
                    rpe_musculaire=rpe[1],
                    rpe_teta=rpe[2],
                )
            )
        Participation.objects.bulk_create(participations)
        # Validée une fois la grille complète : le déclencheur de la base le contrôle.
        valide_le = datetime.datetime.combine(jour, datetime.time(20, 0), tzinfo=FUSEAU)
        Seance.objects.filter(pk=seance.pk).update(statut="validee", validated_at=valide_le)
        return seance, len(participations)

    def _laisser_en_brouillon(self, seance: Seance) -> None:
        """La dernière séance U19 reste en brouillon, grille incomplète (hors des calculs)."""
        Seance.objects.filter(pk=seance.pk).update(statut="brouillon", validated_at=None)
        ids = list(seance.participations.order_by("pk").values_list("pk", flat=True))
        Participation.objects.filter(pk__in=ids[len(ids) // 2 :]).update(
            rpe_cardio=None, rpe_musculaire=None, rpe_teta=None
        )

    # --- sensations --------------------------------------------------------------------

    def _sensations(
        self,
        categorie: Categorie,
        joueurs: list[Joueur],
        indicateurs: list[Indicateur],
        depart: datetime.date,
        archive: Joueur,
    ) -> tuple[int, int]:
        reponses_par_joueur = {
            j.pk: {"niveau": self.rng.gauss(0, 0.8), "coucher": self.rng.gauss(0, 30)}
            for j in joueurs
        }
        frequence = 0.85 if categorie.code == "U19" else 0.7
        entrees: list[EntreeSensations] = []
        for jour in self._jours():
            if jour.weekday() not in categorie.jours_questionnaire:
                continue
            for joueur in joueurs:
                if joueur.pk == archive.pk and jour > depart:
                    continue
                if self.rng.random() <= frequence:
                    entrees.append(EntreeSensations(joueur=joueur, date=jour))
        entrees = EntreeSensations.objects.bulk_create(entrees)

        reponses: list[Reponse] = []
        for entree in entrees:
            profil = reponses_par_joueur[entree.joueur_id]
            en_derive = (self.fin - entree.date).days < JOURS_A_SURVEILLER and (
                entree.joueur_id == self.a_surveiller
            )
            fatigue_du_jour = 0.5 * (self.derniere_charge.get(entree.joueur_id, 5.0) - 5.0)
            for indicateur in indicateurs:
                valeur = self._valeur(indicateur, profil, fatigue_du_jour, en_derive)
                if valeur is None:
                    continue
                reponses.append(Reponse(entree=entree, indicateur=indicateur, valeur=valeur))
        Reponse.objects.bulk_create(reponses, batch_size=2000)
        return len(entrees), len(reponses)

    def _valeur(
        self, indicateur: Indicateur, profil: dict[str, float], fatigue: float, en_derive: bool
    ) -> int | None:
        code = indicateur.code
        if code == "heure_coucher":
            return _borner(22 * 60 + 30 + profil["coucher"] + self.rng.gauss(0, 40), 0, 1439)
        if code == "heure_lever":
            return _borner(6 * 60 + 45 + self.rng.gauss(0, 30), 0, 1439)
        if code == "comprehension" and self.rng.random() < 0.4:
            return None  # facultative (ADR-0010)
        base = 3.0 if indicateur.sens == "bas_bon" else 7.0
        signe = -1 if indicateur.sens == "bas_bon" else 1
        valeur = base + signe * profil["niveau"] + self.rng.gauss(0, 1.1)
        if code == "fatigue":
            valeur += fatigue
        if code == "douleurs":
            valeur += 0.5 * fatigue
        if en_derive and code in {"fatigue", "douleurs"}:
            valeur += 2.5
        if en_derive and code in {"energie", "plaisir", "sommeil"}:
            valeur -= 2.5
        return _borner(valeur, indicateur.borne_min, indicateur.borne_max)
