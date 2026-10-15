"""Historique, correction, en-tête et suppression des séances (US-06, ADR-0008)."""

import datetime
import re

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.utils import timezone

from suivi.calculs import calculer_joueur, parametres
from suivi.models import Categorie, Joueur, Participation, Preparateur, Seance

pytestmark = pytest.mark.django_db

JOUR = datetime.date(2026, 10, 15)
NAISSANCE = datetime.date(2007, 3, 14)


class Monde:
    """Deux préparateurs U19, un préparateur U17 ; une séance U19 validée de 90 minutes."""

    def __init__(self) -> None:
        self.u19 = Categorie.objects.create(code="U19", libelle="U19")
        self.u17 = Categorie.objects.create(code="U17", libelle="U17")
        self.compte19 = User.objects.create_user("p19")
        self.adjoint19 = User.objects.create_user("adjoint19")
        self.compte17 = User.objects.create_user("p17")
        for compte, categorie in [
            (self.compte19, self.u19),
            (self.adjoint19, self.u19),
            (self.compte17, self.u17),
        ]:
            Preparateur.objects.create(user=compte, categorie=categorie)
        self.dupont = self.joueur("Dupont", "Hugo", self.u19)
        self.abel = self.joueur("Abel", "Yanis", self.u19)
        self.leroy = self.joueur("Leroy", "Noah", self.u17)
        self.validee = self.seance(
            JOUR, "validee", (self.dupont, (5, 6, 4)), (self.abel, (7, 7, 7))
        )

    @staticmethod
    def joueur(nom: str, prenom: str, categorie: Categorie) -> Joueur:
        return Joueur.objects.create(
            nom=nom, prenom=prenom, date_naissance=NAISSANCE, categorie_reference=categorie
        )

    def seance(
        self,
        date: datetime.date,
        statut: str = "brouillon",
        *lignes: tuple[Joueur, tuple[int, int, int]],
        categorie: Categorie | None = None,
    ) -> Seance:
        seance = Seance.objects.create(
            categorie_organisatrice=categorie or self.u19,
            date=date,
            type="foot",
            duree_min=90,
            created_by=self.compte19,
            updated_by=self.compte19,
        )
        for joueur, (cardio, musculaire, teta) in lignes:
            Participation.objects.create(
                seance=seance,
                joueur=joueur,
                rpe_cardio=cardio,
                rpe_musculaire=musculaire,
                rpe_teta=teta,
            )
        if statut == "validee":
            seance.statut = "validee"
            seance.validated_at = timezone.now()
            seance.save()
        return seance

    def client(self, compte: User | None = None) -> Client:
        client = Client()
        client.force_login(compte or self.compte19)
        return client


@pytest.fixture
def monde() -> Monde:
    return Monde()


# --- Historique -----------------------------------------------------------------------


def test_l_historique_liste_ses_seances_des_plus_recentes_aux_plus_anciennes(
    monde: Monde,
) -> None:
    ancienne = monde.seance(JOUR - datetime.timedelta(days=3))
    recente = monde.seance(
        JOUR + datetime.timedelta(days=1), "brouillon", (monde.dupont, (1, 1, 1))
    )
    monde.seance(JOUR, categorie=monde.u17)  # autre catégorie

    reponse = monde.client().get("/seances/")
    page = reponse.content.decode()

    assert reponse.status_code == 200
    assert list(reponse.context["page"].object_list) == [recente, monde.validee, ancienne]
    assert [s.nombre_participants for s in reponse.context["page"].object_list] == [1, 2, 0]
    assert page.count("<mark>Brouillon</mark>") == 2
    assert f'href="/seances/{monde.validee.pk}/"' in page
    assert '<a href="/seances/" aria-current="page">Séances</a>' in page


def test_a3_l_historique_ne_montre_aucune_seance_d_une_autre_categorie(monde: Monde) -> None:
    reponse = monde.client(monde.compte17).get("/seances/")

    assert list(reponse.context["page"].object_list) == []
    assert "Aucune séance dans la catégorie." in reponse.content.decode()


def test_l_historique_est_pagine(monde: Monde) -> None:
    for jour in range(30):
        monde.seance(JOUR - datetime.timedelta(days=jour + 1))
    client = monde.client()

    premiere = client.get("/seances/")
    seconde = client.get("/seances/", {"page": "2"})

    assert len(premiere.context["page"].object_list) == 30
    assert "Page 1 sur 2" in premiere.content.decode()
    assert '<a href="?page=2">Plus anciennes</a>' in premiere.content.decode()
    assert len(seconde.context["page"].object_list) == 1
    assert '<a href="?page=1">Plus récentes</a>' in seconde.content.decode()
    assert client.get("/seances/", {"page": "abc"}).context["page"].number == 1
    assert client.get("/seances/", {"page": "99"}).context["page"].number == 2


# --- Page d'une séance validée et correction -------------------------------------------


def test_une_seance_validee_montre_sa_trace_et_le_lien_de_correction(monde: Monde) -> None:
    page = monde.client().get(f"/seances/{monde.validee.pk}/").content.decode()

    assert re.search(r"Dernière modification le \d\d/\d\d/\d{4} à \d\d:\d\d par p19\.", page)
    assert f'href="/seances/{monde.validee.pk}/corriger/"' in page
    assert f'href="/seances/{monde.validee.pk}/modifier/"' in page
    assert f'href="/seances/{monde.validee.pk}/supprimer/"' in page


def test_la_correction_ouvre_la_grille_remplie_sans_les_charges(monde: Monde) -> None:
    reponse = monde.client().get(f"/seances/{monde.validee.pk}/corriger/", {"q": "ler"})
    page = reponse.content.decode()

    assert reponse.status_code == 200
    assert "Corriger la grille RPE" in page
    assert "Enregistrer les corrections" in page and "Valider la séance" not in page
    assert page.count('class="rpe"') >= 6
    assert 'value="5"' in page and 'value="7"' in page
    assert reponse.context["validees"] == []
    assert "grille.js" in page
    # Un joueur de l'annuaire s'ajoute avec ses trois RPE, saisis sur sa ligne.
    assert f'form="ajout-{monde.leroy.pk}" name="rpe_cardio"' in page
    assert f'id="ajout-{monde.leroy.pk}"' in page


def test_un_brouillon_se_corrige_sur_sa_propre_page(monde: Monde) -> None:
    brouillon = monde.seance(JOUR)

    reponse = monde.client().get(f"/seances/{brouillon.pk}/corriger/")

    assert reponse.status_code == 302
    assert reponse["Location"] == f"/seances/{brouillon.pk}/"


@pytest.mark.parametrize("action", ["corriger", "modifier", "supprimer"])
def test_a3_une_seance_d_une_autre_categorie_ne_se_corrige_pas(monde: Monde, action: str) -> None:
    client = monde.client(monde.compte17)

    assert client.get(f"/seances/{monde.validee.pk}/{action}/").status_code == 404
    if action != "corriger":
        assert client.post(f"/seances/{monde.validee.pk}/{action}/", {}).status_code == 404
    assert Seance.objects.filter(pk=monde.validee.pk, duree_min=90).exists()


# --- Modification de l'en-tête --------------------------------------------------------


def test_le_formulaire_de_l_en_tete_est_pre_rempli(monde: Monde) -> None:
    page = monde.client().get(f"/seances/{monde.validee.pk}/modifier/").content.decode()

    assert "Modifier la séance du 15/10/2026" in page
    assert 'value="2026-10-15"' in page
    assert 'value="90"' in page
    assert "validée : ses charges sont recalculées" in page


def test_l_en_tete_d_une_seance_validee_se_corrige_et_les_charges_suivent(monde: Monde) -> None:
    client = monde.client()

    reponse = client.post(
        f"/seances/{monde.validee.pk}/modifier/",
        {"date": "2026-10-14", "type": "musculation", "duree_min": "60", "statut": "brouillon"},
    )

    assert reponse["Location"] == f"/seances/{monde.validee.pk}/"
    monde.validee.refresh_from_db()
    assert (monde.validee.date, monde.validee.type, monde.validee.duree_min) == (
        datetime.date(2026, 10, 14),
        "musculation",
        60,
    )
    assert monde.validee.statut == "validee"
    assert monde.validee.updated_by == monde.compte19
    page = client.get(reponse["Location"])
    assert "L’en-tête de la séance est modifié." in page.content.decode()
    # Calculée à la main : (5 + 6 + 4) / 3 × 60 × 10 = 3000, désormais le 14.
    charges = {p.joueur.nom: charge for p, charge in page.context["validees"]}
    assert charges["Dupont"] == pytest.approx(3000.0, rel=1e-9)
    jours = calculer_joueur(monde.dupont.pk, JOUR, parametres())
    assert [(j.jour, j.charge_jour) for j in jours] == [
        (datetime.date(2026, 10, 14), pytest.approx(3000.0, rel=1e-9)),
        (JOUR, 0.0),
    ]


@pytest.mark.parametrize(
    ("champs", "champ"),
    [
        ({"duree_min": "0"}, "duree_min"),
        ({"duree_min": "301"}, "duree_min"),
        ({"type": "course"}, "type"),
        ({"date": ""}, "date"),
    ],
    ids=["duree-nulle", "duree-trop-longue", "type-inconnu", "date-vide"],
)
def test_d1_un_en_tete_invalide_ne_modifie_rien(
    monde: Monde, champs: dict[str, str], champ: str
) -> None:
    donnees = {"date": "2026-10-14", "type": "foot", "duree_min": "60", **champs}

    reponse = monde.client().post(f"/seances/{monde.validee.pk}/modifier/", donnees)

    assert reponse.status_code == 200
    assert reponse.context["form"].errors[champ]
    assert "Modifier la séance du 15/10/2026" in reponse.content.decode()
    monde.validee.refresh_from_db()
    assert (monde.validee.date, monde.validee.duree_min) == (JOUR, 90)


# --- Suppression confirmée ------------------------------------------------------------


def test_la_suppression_demande_une_confirmation(monde: Monde) -> None:
    reponse = monde.client().get(f"/seances/{monde.validee.pk}/supprimer/")
    page = reponse.content.decode()

    assert reponse.status_code == 200
    assert "Supprimer la séance du jeudi 15 octobre 2026 ?" in page
    assert "2 participants" in page
    assert "La suppression est définitive" in page
    assert Seance.objects.filter(pk=monde.validee.pk).exists()


@pytest.mark.parametrize("statut", ["validee", "brouillon"])
def test_la_suppression_retire_la_seance_et_ses_participations(monde: Monde, statut: str) -> None:
    autre = monde.seance(JOUR, "validee", (monde.dupont, (2, 2, 2)))
    cible = monde.validee if statut == "validee" else monde.seance(JOUR, "brouillon")
    client = monde.client()

    reponse = client.post(f"/seances/{cible.pk}/supprimer/")

    assert reponse["Location"] == "/seances/"
    assert not Seance.objects.filter(pk=cible.pk).exists()
    assert not Participation.objects.filter(seance_id=cible.pk).exists()
    assert Participation.objects.filter(seance=autre).count() == 1
    assert "La séance du 15/10/2026 est supprimée." in client.get("/seances/").content.decode()


def test_une_seance_supprimee_ne_compte_plus_dans_la_charge(monde: Monde) -> None:
    monde.client().post(f"/seances/{monde.validee.pk}/supprimer/")

    assert calculer_joueur(monde.dupont.pk, JOUR, parametres()) == []


# --- Traçabilité (ADR-0008, Q4) -------------------------------------------------------


def test_chaque_correction_enregistre_sa_date_et_son_auteur(monde: Monde) -> None:
    adjoint = monde.client(monde.adjoint19)
    avant = monde.validee.updated_at

    adjoint.post(
        f"/seances/{monde.validee.pk}/modifier/",
        {"date": "2026-10-15", "type": "foot", "duree_min": "80"},
    )
    monde.validee.refresh_from_db()
    assert monde.validee.updated_by == monde.adjoint19
    assert monde.validee.updated_at > avant

    avant = monde.validee.updated_at
    participations = list(Participation.objects.filter(seance=monde.validee).order_by("pk"))
    donnees = {
        f"p{p.pk}_{champ}": str(getattr(p, champ))
        for p in participations
        for champ in ("rpe_cardio", "rpe_musculaire", "rpe_teta")
    }
    donnees[f"p{participations[0].pk}_rpe_cardio"] = "8"
    monde.client().post(f"/seances/{monde.validee.pk}/grille/", donnees)
    monde.validee.refresh_from_db()
    participations[0].refresh_from_db()
    participations[1].refresh_from_db()
    assert monde.validee.updated_by == monde.compte19
    assert monde.validee.updated_at > avant
    assert participations[0].updated_by == monde.compte19
    assert participations[1].updated_by is None  # ligne inchangée


@pytest.mark.parametrize("action", ["supprimer", "modifier"])
def test_rien_ne_change_par_une_simple_lecture(monde: Monde, action: str) -> None:
    monde.client().get(f"/seances/{monde.validee.pk}/{action}/")

    monde.validee.refresh_from_db()
    assert monde.validee.duree_min == 90
