"""Grille RPE : brouillon puis validation, charges de la séance validée (US-04, US-05, D1, A3)."""

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
CHAMPS = ("rpe_cardio", "rpe_musculaire", "rpe_teta")


class Monde:
    """Une séance U19 de 90 minutes en brouillon : Abel, Dupont (U19) et Leroy (U17, invité)."""

    def __init__(self) -> None:
        self.u19 = Categorie.objects.create(code="U19", libelle="U19")
        self.u17 = Categorie.objects.create(code="U17", libelle="U17")
        self.compte19 = User.objects.create_user("p19")
        self.compte17 = User.objects.create_user("p17")
        Preparateur.objects.create(user=self.compte19, categorie=self.u19)
        Preparateur.objects.create(user=self.compte17, categorie=self.u17)
        self.seance = Seance.objects.create(
            categorie_organisatrice=self.u19, date=JOUR, type="foot", duree_min=90
        )
        self.abel = self.participation("Abel", "Yanis", self.u19)
        self.dupont = self.participation("Dupont", "Hugo", self.u19)
        self.leroy = self.participation("Leroy", "Noah", self.u17)

    def participation(self, nom: str, prenom: str, categorie: Categorie) -> Participation:
        joueur = Joueur.objects.create(
            nom=nom, prenom=prenom, date_naissance=NAISSANCE, categorie_reference=categorie
        )
        return Participation.objects.create(seance=self.seance, joueur=joueur)

    def client(self, compte: User | None = None) -> Client:
        client = Client()
        client.force_login(compte or self.compte19)
        return client

    def grille(self, **valeurs: tuple[str, str, str]) -> dict[str, str]:
        """Données envoyées par la grille ; une ligne absente de `valeurs` reste vide."""
        donnees: dict[str, str] = {}
        for nom in ("abel", "dupont", "leroy"):
            participation: Participation = getattr(self, nom)
            for champ, valeur in zip(CHAMPS, valeurs.get(nom, ("", "", "")), strict=True):
                donnees[f"p{participation.pk}_{champ}"] = valeur
        return donnees

    def poster(
        self,
        donnees: dict[str, str],
        action: str = "enregistrer",
        client: Client | None = None,
        compte: User | None = None,
    ):  # noqa: ANN201
        client = client or self.client(compte)
        return client.post(f"/seances/{self.seance.pk}/grille/", {**donnees, action: ""})


@pytest.fixture
def monde() -> Monde:
    return Monde()


def _rpe(participation: Participation) -> tuple[int | None, ...]:
    participation.refresh_from_db()
    return tuple(getattr(participation, champ) for champ in CHAMPS)


COMPLETE = {"abel": ("5", "6", "4"), "dupont": ("7", "7", "7"), "leroy": ("0", "10", "3")}


# --- La grille ------------------------------------------------------------------------


def test_la_grille_a_trois_cases_par_participant_dans_l_ordre_de_lecture(monde: Monde) -> None:
    page = monde.client().get(f"/seances/{monde.seance.pk}/").content.decode()

    noms = re.findall(r'name="(p\d+_rpe_\w+)"', page)
    attendus = [
        f"p{participation.pk}_{champ}"
        for participation in (monde.abel, monde.dupont, monde.leroy)
        for champ in CHAMPS
    ]
    # La touche Tab suit l'ordre du document : cardio, musculaire, TETA, puis la ligne suivante.
    assert noms == attendus
    assert page.count('inputmode="numeric"') == 9
    assert 'aria-label="RPE cardio de Hugo Dupont"' in page
    assert 'aria-label="RPE TETA de Noah Leroy"' in page
    assert "Leroy</strong> Noah <small>(U17)</small>" in page
    assert '<script src="/static/suivi/js/grille.js" defer></script>' in page
    assert "Enregistrer le brouillon" in page and "Valider la séance" in page


def test_la_grille_reprend_les_valeurs_enregistrees_avec_leur_couleur(monde: Monde) -> None:
    Participation.objects.filter(pk=monde.dupont.pk).update(rpe_cardio=8)

    page = monde.client().get(f"/seances/{monde.seance.pk}/").content.decode()

    case = re.search(rf'<input[^>]*name="p{monde.dupont.pk}_rpe_cardio"[^>]*>', page)
    assert case is not None
    assert 'value="8"' in case.group(0)
    assert 'data-niveau="8"' in case.group(0)


# --- Brouillon (US-05) ----------------------------------------------------------------


def test_un_brouillon_s_enregistre_avec_des_rpe_manquants(monde: Monde) -> None:
    avant_leroy = Participation.objects.get(pk=monde.leroy.pk).updated_at
    client = monde.client()

    reponse = monde.poster(monde.grille(abel=("5", "", "4"), dupont=("7", "7", "7")), client=client)

    assert reponse.status_code == 302
    assert reponse["Location"] == f"/seances/{monde.seance.pk}/"
    assert _rpe(monde.abel) == (5, None, 4)
    assert _rpe(monde.dupont) == (7, 7, 7)
    assert _rpe(monde.leroy) == (None, None, None)
    monde.seance.refresh_from_db()
    assert monde.seance.statut == "brouillon"
    assert monde.seance.validated_at is None
    assert monde.seance.updated_by == monde.compte19
    assert monde.abel.updated_by == monde.dupont.updated_by == monde.compte19
    # Ligne inchangée : ni sa date ni son auteur de modification ne bougent.
    assert monde.leroy.updated_by is None
    assert monde.leroy.updated_at == avant_leroy
    assert "Le brouillon est enregistré." in client.get(reponse["Location"]).content.decode()


def test_c5_un_brouillon_n_entre_dans_aucun_calcul(monde: Monde) -> None:
    monde.poster(monde.grille(**COMPLETE))

    assert calculer_joueur(monde.dupont.joueur_id, JOUR, parametres()) == []
    page = monde.client().get(f"/seances/{monde.seance.pk}/").content.decode()
    assert "Charge" not in page


def test_une_case_videe_dans_un_brouillon_est_effacee(monde: Monde) -> None:
    Participation.objects.filter(pk=monde.abel.pk).update(rpe_cardio=5, rpe_teta=4)

    monde.poster(monde.grille(abel=("", "", "4")))

    assert _rpe(monde.abel) == (None, None, 4)


# --- Validation (US-05) ---------------------------------------------------------------


def test_une_grille_complete_valide_la_seance_et_affiche_les_charges(monde: Monde) -> None:
    client = monde.client()

    reponse = monde.poster(monde.grille(**COMPLETE), action="valider", client=client)

    assert reponse["Location"] == f"/seances/{monde.seance.pk}/"
    monde.seance.refresh_from_db()
    assert monde.seance.statut == "validee"
    assert monde.seance.validated_at is not None
    assert monde.seance.updated_by == monde.compte19
    assert _rpe(monde.leroy) == (0, 10, 3)
    page_reponse = client.get(reponse["Location"])
    page = page_reponse.content.decode()
    assert "La séance est validée : les charges sont calculées." in page
    # Valeurs calculées à la main : (5 + 6 + 4) / 3 × 90 × 10 = 4500, 7 × 90 × 10 = 6300,
    # (0 + 10 + 3) / 3 × 90 × 10 = 3900.
    charges = {p.joueur.nom: charge for p, charge in page_reponse.context["validees"]}
    assert charges == {
        "Abel": pytest.approx(4500.0, rel=1e-9),
        "Dupont": pytest.approx(6300.0, rel=1e-9),
        "Leroy": pytest.approx(3900.0, rel=1e-9),
    }
    assert re.search(r'<td class="charge">4\s500</td>', page)
    assert re.search(r'<td class="charge">6\s300</td>', page)
    assert 'name="p' not in page  # plus aucune case de saisie
    assert '<span class="rpe" data-niveau="10">10</span>' in page


def test_e1_une_seance_validee_entre_dans_le_calcul_du_joueur(monde: Monde) -> None:
    monde.poster(monde.grille(**COMPLETE), action="valider")

    jours = calculer_joueur(monde.dupont.joueur_id, JOUR, parametres())

    assert [jour.jour for jour in jours] == [JOUR]
    assert jours[0].charge_jour == pytest.approx(6300.0, rel=1e-9)


def test_la_validation_exige_les_trois_rpe_de_chaque_participant(monde: Monde) -> None:
    reponse = monde.poster(
        monde.grille(abel=("5", "6", "4"), dupont=("7", "", "7"), leroy=("", "", "")),
        action="valider",
    )
    page = reponse.content.decode()

    assert reponse.status_code == 200
    assert "4 case(s) vide(s)" in page
    assert page.count('aria-invalid="true"') == 4
    # Rien n'est enregistré, et la saisie n'est pas perdue.
    assert _rpe(monde.abel) == (None, None, None)
    monde.seance.refresh_from_db()
    assert monde.seance.statut == "brouillon"
    assert re.search(rf'name="p{monde.abel.pk}_rpe_cardio"[^>]*value="5"', page) or re.search(
        rf'value="5"[^>]*name="p{monde.abel.pk}_rpe_cardio"', page
    )


def test_une_seance_sans_participant_ne_se_valide_pas(monde: Monde) -> None:
    Participation.objects.all().delete()

    reponse = monde.poster({}, action="valider")

    assert reponse.status_code == 200
    monde.seance.refresh_from_db()
    assert monde.seance.statut == "brouillon"
    page = reponse.content.decode()
    assert "Une séance sans participant ne se valide pas." in page
    assert "Aucun participant" in page


def test_la_validation_sans_participant_est_refusee_par_le_formulaire(monde: Monde) -> None:
    from suivi.forms import GrilleRpeForm

    grille = GrilleRpeForm({}, participations=[], valider=True)

    assert not grille.is_valid()
    assert grille.non_field_errors() == ["Une séance sans participant ne se valide pas."]


# --- D1 : valeur hors échelle refusée à la saisie -------------------------------------


@pytest.mark.parametrize("valeur", ["11", "-1", "abc", "1,5", "3.5", "100"])
@pytest.mark.parametrize("action", ["enregistrer", "valider"])
def test_d1_une_valeur_hors_echelle_est_refusee_sans_rien_enregistrer(
    monde: Monde, valeur: str, action: str
) -> None:
    grille = {**COMPLETE, "dupont": (valeur, "7", "7")}

    reponse = monde.poster(monde.grille(**grille), action=action)
    page = reponse.content.decode()

    assert reponse.status_code == 200
    assert "RPE cardio de Hugo Dupont : " in page
    assert re.search(rf'<input[^>]*name="p{monde.dupont.pk}_rpe_cardio"[^>]*>', page)
    case = re.search(rf'<input[^>]*name="p{monde.dupont.pk}_rpe_cardio"[^>]*>', page)
    assert case is not None and 'aria-invalid="true"' in case.group(0)
    assert 'data-niveau="invalide"' in case.group(0)
    assert _rpe(monde.abel) == (None, None, None)
    monde.seance.refresh_from_db()
    assert monde.seance.statut == "brouillon"


@pytest.mark.parametrize(("saisie", "attendu"), [("0", 0), ("10", 10), (" 7 ", 7)])
def test_d1_les_bornes_de_l_echelle_sont_acceptees(monde: Monde, saisie: str, attendu: int) -> None:
    monde.poster(monde.grille(abel=(saisie, "", "")))

    assert _rpe(monde.abel)[0] == attendu


# --- Garde-fous -----------------------------------------------------------------------


def test_une_grille_perimee_est_refusee(monde: Monde) -> None:
    donnees = monde.grille(**COMPLETE)
    del donnees[f"p{monde.leroy.pk}_rpe_teta"]  # participant ajouté après l'ouverture

    reponse = monde.poster(donnees, action="valider")

    assert reponse.status_code == 200
    assert "Les participants ont changé depuis l’ouverture de la grille" in reponse.content.decode()
    assert _rpe(monde.abel) == (None, None, None)


def test_une_seance_validee_ne_se_modifie_pas_par_la_grille(monde: Monde) -> None:
    monde.poster(monde.grille(**COMPLETE), action="valider")
    client = monde.client()

    reponse = client.post(
        f"/seances/{monde.seance.pk}/grille/", {**monde.grille(**COMPLETE), "abel": ""}
    )

    assert reponse["Location"] == f"/seances/{monde.seance.pk}/"
    assert _rpe(monde.abel) == (5, 6, 4)
    page = client.get(reponse["Location"]).content.decode()
    assert "Cette séance est validée : ses RPE ne se modifient plus ici." in page


def test_a3_l_autre_preparateur_ne_saisit_rien_dans_ses_seances(monde: Monde) -> None:
    reponse = monde.poster(monde.grille(**COMPLETE), action="valider", compte=monde.compte17)

    assert reponse.status_code == 404
    assert _rpe(monde.dupont) == (None, None, None)
    monde.seance.refresh_from_db()
    assert monde.seance.statut == "brouillon"


def test_a3_une_case_d_une_autre_seance_est_ignoree(monde: Monde) -> None:
    autre = Seance.objects.create(
        categorie_organisatrice=monde.u17, date=JOUR, type="foot", duree_min=60
    )
    etrangere = Participation.objects.create(seance=autre, joueur=monde.leroy.joueur)

    monde.poster({**monde.grille(**COMPLETE), f"p{etrangere.pk}_rpe_cardio": "9"})

    assert _rpe(etrangere) == (None, None, None)
    assert _rpe(monde.dupont) == (7, 7, 7)


def test_la_grille_ne_s_enregistre_jamais_par_une_simple_lecture(monde: Monde) -> None:
    assert monde.client().get(f"/seances/{monde.seance.pk}/grille/").status_code == 405


def test_une_seance_validee_s_affiche_sans_grille_ni_script(monde: Monde) -> None:
    for participation in (monde.abel, monde.dupont, monde.leroy):
        Participation.objects.filter(pk=participation.pk).update(
            rpe_cardio=1, rpe_musculaire=2, rpe_teta=3
        )
    Seance.objects.filter(pk=monde.seance.pk).update(statut="validee", validated_at=timezone.now())

    page = monde.client().get(f"/seances/{monde.seance.pk}/").content.decode()

    assert "grille.js" not in page
    assert "Participants (3)" in page
    # (1 + 2 + 3) / 3 × 90 × 10 = 1800 pour chacun.
    assert len(re.findall(r'<td class="charge">1\s800</td>', page)) == 3
