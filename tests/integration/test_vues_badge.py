"""Badge Reçu / Manquant dans la grille d'une séance (US-08, F10, R22, ADR-0017, E2)."""

import datetime
import re

import pytest
from django.contrib.auth.models import User
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from suivi.models import (
    Categorie,
    EntreeSensations,
    Joueur,
    Participation,
    Preparateur,
    Seance,
    StatutSeance,
)

pytestmark = pytest.mark.django_db

JOUR = datetime.date(2026, 10, 15)  # un jeudi (weekday 3)
NAISSANCE = datetime.date(2007, 3, 14)
BADGE = re.compile(r'<span class="badge[^"]*"[^>]*>([^<]+)</span>')


class Monde:
    """Séance U19 du jeudi : Abel et Dupont (U19), Leroy (U17, invité)."""

    def __init__(self) -> None:
        self.u19 = Categorie.objects.create(code="U19", libelle="U19")
        self.u17 = Categorie.objects.create(code="U17", libelle="U17")
        self.compte = User.objects.create_user("p19")
        Preparateur.objects.create(user=self.compte, categorie=self.u19)
        self.seance = Seance.objects.create(
            categorie_organisatrice=self.u19, date=JOUR, type="foot", duree_min=90
        )
        self.abel = self.participation("Abel", self.u19)
        self.dupont = self.participation("Dupont", self.u19)
        self.leroy = self.participation("Leroy", self.u17)

    def participation(self, nom: str, categorie: Categorie) -> Participation:
        joueur = Joueur.objects.create(
            nom=nom, prenom="Test", date_naissance=NAISSANCE, categorie_reference=categorie
        )
        return Participation.objects.create(seance=self.seance, joueur=joueur)

    def entree(self, participation: Participation, jour: datetime.date = JOUR) -> None:
        EntreeSensations.objects.create(joueur=participation.joueur, date=jour)

    def valider(self) -> None:
        for participation in (self.abel, self.dupont, self.leroy):
            Participation.objects.filter(pk=participation.pk).update(
                rpe_cardio=5, rpe_musculaire=5, rpe_teta=5
            )
        Seance.objects.filter(pk=self.seance.pk).update(
            statut=StatutSeance.VALIDEE, validated_at=timezone.now()
        )

    def page(self, chemin: str = "") -> str:
        client = Client()
        client.force_login(self.compte)
        reponse = client.get(f"/seances/{self.seance.pk}/{chemin}")
        assert reponse.status_code == 200
        return reponse.content.decode()


def _badge(page: str, nom: str) -> str:
    """Texte du badge de la ligne du joueur dans la grille (pas dans la liste des participants)."""
    lignes = [ligne for ligne in re.findall(r"<tr>.*?</tr>", page, re.DOTALL) if nom in ligne]
    badges = [BADGE.findall(ligne) for ligne in lignes if "badge" in ligne]
    assert len(badges) == 1, f"un seul badge attendu pour {nom}, trouvé {badges}"
    assert len(badges[0]) == 1
    return badges[0][0].strip()


@pytest.fixture
def monde(monkeypatch: pytest.MonkeyPatch) -> Monde:
    monkeypatch.setattr("suivi.views.staff.aujourd_hui", lambda: JOUR)
    return Monde()


@pytest.mark.parametrize("vue", ["brouillon", "correction"])
def test_e2_le_badge_passe_a_recu_quand_le_joueur_a_repondu_le_jour_de_la_seance(
    monde: Monde, vue: str
) -> None:
    monde.entree(monde.abel)
    if vue == "correction":
        monde.valider()

    page = monde.page("corriger/" if vue == "correction" else "")

    assert _badge(page, "Abel") == "Reçu"
    assert _badge(page, "Dupont") == "Manquant"


def test_le_badge_figure_aussi_sur_la_seance_validee(monde: Monde) -> None:
    monde.entree(monde.abel)
    monde.valider()

    page = monde.page()

    assert "Charge" in page
    assert _badge(page, "Abel") == "Reçu"
    assert _badge(page, "Dupont") == "Manquant"


def test_une_entree_d_un_autre_jour_ne_donne_pas_recu(monde: Monde) -> None:
    monde.entree(monde.abel, JOUR - datetime.timedelta(days=1))
    monde.entree(monde.abel, JOUR + datetime.timedelta(days=1))

    assert _badge(monde.page(), "Abel") == "Manquant"


def test_r22_un_jour_hors_des_jours_de_questionnaire_donne_un_tiret(monde: Monde) -> None:
    monde.u19.jours_questionnaire = [0, 1, 2]  # lundi à mercredi ; la séance est un jeudi
    monde.u19.save()

    page = monde.page()

    assert _badge(page, "Abel") == "—"
    assert _badge(page, "Dupont") == "—"


def test_r22_une_entree_un_jour_hors_questionnaire_reste_recue(monde: Monde) -> None:
    monde.u19.jours_questionnaire = [0, 1, 2]
    monde.u19.save()
    monde.entree(monde.abel)

    assert _badge(monde.page(), "Abel") == "Reçu"


def test_une_seance_a_venir_n_a_pas_de_manquant(
    monde: Monde, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("suivi.views.staff.aujourd_hui", lambda: JOUR - datetime.timedelta(days=2))

    assert _badge(monde.page(), "Abel") == "—"


def test_le_jour_meme_le_manquant_reste_affiche(monde: Monde) -> None:
    # Le joueur peut encore répondre jusqu'à 23 h 59 (ADR-0008).
    assert _badge(monde.page(), "Abel") == "Manquant"


def test_a3_le_badge_d_un_joueur_invite_ne_revele_rien_de_son_entree(monde: Monde) -> None:
    # Les entrées d'un joueur d'une autre catégorie ne sont jamais lisibles (ADR-0005).
    sans = _badge(monde.page(), "Leroy")
    monde.entree(monde.leroy)
    avec = _badge(monde.page(), "Leroy")

    assert sans == avec == "—"


def test_le_badge_suit_les_jours_de_la_categorie_du_joueur_pas_de_celle_de_la_seance(
    monde: Monde,
) -> None:
    monde.u17.jours_questionnaire = [3]
    monde.u17.save()
    monde.u19.jours_questionnaire = [0]
    monde.u19.save()

    page = monde.page()

    assert _badge(page, "Abel") == "—"  # U19 : lundi seulement
    assert _badge(page, "Leroy") == "—"  # invité : jamais de badge


def test_le_badge_ne_fait_pas_une_requete_par_joueur(monde: Monde) -> None:
    def requetes() -> int:
        with CaptureQueriesContext(connection) as contexte:
            monde.page()
        return len(contexte)

    avant = requetes()
    for numero in range(20):
        joueur = Joueur.objects.create(
            nom=f"Extra{numero:02d}",
            prenom="Test",
            date_naissance=NAISSANCE,
            categorie_reference=monde.u19,
        )
        Participation.objects.create(seance=monde.seance, joueur=joueur)

    assert requetes() == avant
