"""Création d'une séance et de ses participants (US-03, R24, A3, D1)."""

import datetime

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.utils import timezone

from suivi.models import Categorie, Joueur, Participation, Preparateur, Seance

pytestmark = pytest.mark.django_db

JOUR = datetime.date(2026, 10, 15)
NAISSANCE = datetime.date(2007, 3, 14)


class Monde:
    """Deux catégories et leurs préparateurs ; Leroy (U17) peut s'entraîner avec les U19."""

    def __init__(self) -> None:
        self.u19 = Categorie.objects.create(code="U19", libelle="U19")
        self.u17 = Categorie.objects.create(code="U17", libelle="U17")
        self.compte19 = User.objects.create_user("p19")
        self.compte17 = User.objects.create_user("p17")
        Preparateur.objects.create(user=self.compte19, categorie=self.u19)
        Preparateur.objects.create(user=self.compte17, categorie=self.u17)
        self.dupont = self.joueur("Dupont", "Hugo", self.u19)
        self.abel = self.joueur("Abel", "Yanis", self.u19)
        self.bernard = self.joueur("Bernard", "Léo", self.u19, actif=False)
        self.leroy = self.joueur("Leroy", "Noah", self.u17, naissance=datetime.date(2009, 1, 23))

    @staticmethod
    def joueur(
        nom: str,
        prenom: str,
        categorie: Categorie,
        actif: bool = True,
        naissance: datetime.date = NAISSANCE,
    ) -> Joueur:
        return Joueur.objects.create(
            nom=nom,
            prenom=prenom,
            date_naissance=naissance,
            categorie_reference=categorie,
            actif=actif,
        )

    def seance(self, categorie: Categorie | None = None, *joueurs: Joueur) -> Seance:
        seance = Seance.objects.create(
            categorie_organisatrice=categorie or self.u19, date=JOUR, type="foot", duree_min=90
        )
        for joueur in joueurs:
            Participation.objects.create(seance=seance, joueur=joueur)
        return seance

    def seance_validee(self) -> Seance:
        seance = Seance.objects.create(
            categorie_organisatrice=self.u19, date=JOUR, type="foot", duree_min=90
        )
        Participation.objects.create(
            seance=seance, joueur=self.dupont, rpe_cardio=5, rpe_musculaire=6, rpe_teta=4
        )
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


def _entete(**champs: object) -> dict[str, object]:
    return {"date": "2026-10-15", "type": "foot", "duree_min": "90", **champs}


def _nombres() -> tuple[int, int]:
    return Seance.objects.count(), Participation.objects.count()


# --- Création : formulaire pré-rempli ------------------------------------------------


def test_le_formulaire_est_pre_rempli_avec_les_joueurs_actifs_de_sa_categorie(
    monde: Monde, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("suivi.views.staff.aujourd_hui", lambda: datetime.date(2026, 10, 14))

    reponse = monde.client().get("/seances/nouvelle/")
    form = reponse.context["form"]
    page = reponse.content.decode()

    assert reponse.status_code == 200
    assert list(form.fields["participants"].queryset) == [monde.abel, monde.dupont]
    assert form.initial["participants"] == [monde.abel.pk, monde.dupont.pk]
    assert form.initial["date"] == datetime.date(2026, 10, 14)
    assert 'value="2026-10-14"' in page
    assert page.count('type="checkbox"') == 2
    assert page.count("checked") == 2
    assert "Bernard" not in page  # archivé
    assert "Leroy" not in page  # autre catégorie
    assert '<option value="foot" selected>Foot</option>' in page
    assert "---------" not in page
    assert 'min="1"' in page and 'max="300"' in page


def test_la_navigation_signale_la_nouvelle_seance(monde: Monde) -> None:
    page = monde.client().get("/seances/nouvelle/").content.decode()

    assert '<a href="/seances/nouvelle/" aria-current="page">Nouvelle séance</a>' in page


# --- Création : enregistrement ---------------------------------------------------------


def test_une_seance_est_creee_en_brouillon_avec_ses_participants(monde: Monde) -> None:
    client = monde.client()

    reponse = client.post(
        "/seances/nouvelle/", _entete(participants=[monde.abel.pk, monde.dupont.pk])
    )

    seance = Seance.objects.get()
    assert reponse.status_code == 302
    assert reponse["Location"] == f"/seances/{seance.pk}/"
    assert seance.categorie_organisatrice == monde.u19
    assert (seance.date, seance.type, seance.duree_min) == (JOUR, "foot", 90)
    assert seance.statut == "brouillon"
    assert seance.validated_at is None
    assert seance.created_by == seance.updated_by == monde.compte19
    participations = Participation.objects.filter(seance=seance)
    assert {p.joueur for p in participations} == {monde.abel, monde.dupont}
    for participation in participations:
        assert (participation.rpe_cardio, participation.rpe_musculaire) == (None, None)
        assert participation.rpe_teta is None
        assert participation.updated_by == monde.compte19
    assert "La séance est créée en brouillon." in client.get(reponse["Location"]).content.decode()


def test_un_absent_decoche_ne_participe_pas(monde: Monde) -> None:
    monde.client().post("/seances/nouvelle/", _entete(participants=[monde.abel.pk]))

    assert [p.joueur for p in Participation.objects.all()] == [monde.abel]


def test_une_seance_peut_etre_creee_sans_participant(monde: Monde) -> None:
    reponse = monde.client().post("/seances/nouvelle/", _entete())

    assert reponse.status_code == 302
    assert _nombres() == (1, 0)


def test_le_statut_et_la_categorie_ne_se_choisissent_pas_dans_la_requete(monde: Monde) -> None:
    donnees = _entete(statut="validee", categorie_organisatrice=monde.u17.pk, validated_at="x")

    monde.client().post("/seances/nouvelle/", donnees)

    seance = Seance.objects.get()
    assert seance.categorie_organisatrice == monde.u19
    assert seance.statut == "brouillon"


@pytest.mark.parametrize("cible", ["leroy", "bernard"], ids=["autre-categorie", "archive"])
def test_a3_un_participant_hors_de_ses_joueurs_actifs_est_refuse(monde: Monde, cible: str) -> None:
    joueur: Joueur = getattr(monde, cible)

    reponse = monde.client().post(
        "/seances/nouvelle/", _entete(participants=[monde.dupont.pk, joueur.pk])
    )

    assert reponse.status_code == 200
    assert reponse.context["form"].errors["participants"]
    assert _nombres() == (0, 0)


# --- D1 : en-tête refusé à la saisie --------------------------------------------------


@pytest.mark.parametrize(
    ("champs", "champ"),
    [
        ({"duree_min": "0"}, "duree_min"),
        ({"duree_min": "-10"}, "duree_min"),
        ({"duree_min": "301"}, "duree_min"),
        ({"duree_min": ""}, "duree_min"),
        ({"duree_min": "1,5"}, "duree_min"),
        ({"type": "course"}, "type"),
        ({"type": ""}, "type"),
        ({"date": "2026-02-30"}, "date"),
        ({"date": ""}, "date"),
    ],
    ids=[
        "duree-nulle",
        "duree-negative",
        "duree-trop-longue",
        "duree-vide",
        "duree-decimale",
        "type-inconnu",
        "type-vide",
        "date-impossible",
        "date-vide",
    ],
)
def test_d1_un_en_tete_invalide_est_refuse_sans_rien_enregistrer(
    monde: Monde, champs: dict[str, str], champ: str
) -> None:
    reponse = monde.client().post(
        "/seances/nouvelle/", _entete(participants=[monde.dupont.pk], **champs)
    )

    assert reponse.status_code == 200
    assert reponse.context["form"].errors[champ]
    assert '<small class="erreur">' in reponse.content.decode()
    assert _nombres() == (0, 0)


@pytest.mark.parametrize("duree", ["1", "300"])
def test_d1_les_bornes_de_la_duree_sont_acceptees(monde: Monde, duree: str) -> None:
    monde.client().post("/seances/nouvelle/", _entete(duree_min=duree))

    assert Seance.objects.get().duree_min == int(duree)


# --- Page de la séance ----------------------------------------------------------------


def test_la_page_montre_l_en_tete_et_les_participants_tries(monde: Monde) -> None:
    seance = monde.seance(None, monde.dupont, monde.leroy, monde.abel)

    reponse = monde.client().get(f"/seances/{seance.pk}/")
    page = reponse.content.decode()

    assert reponse.status_code == 200
    assert "Séance du jeudi 15 octobre 2026" in page
    assert "Foot · 90 min · Brouillon" in page
    assert "Participants (3)" in page
    assert [p.joueur for p in reponse.context["participations"]] == [
        monde.abel,
        monde.dupont,
        monde.leroy,
    ]
    assert "<td>U17</td>" in page


def test_a3_l_invite_n_est_montre_que_par_son_nom_et_sa_categorie(monde: Monde) -> None:
    autre = monde.seance(monde.u17, monde.leroy)
    seance = monde.seance(None, monde.leroy)

    page = monde.client().get(f"/seances/{seance.pk}/").content.decode()

    assert "Leroy" in page
    assert "23/01/2009" not in page and "2009" not in page
    assert f"/seances/{autre.pk}/" not in page


@pytest.mark.parametrize("compte", ["compte17", None], ids=["autre-categorie", "inexistante"])
def test_a3_une_seance_d_une_autre_categorie_est_introuvable(
    monde: Monde, compte: str | None
) -> None:
    seance = monde.seance(None, monde.dupont)
    if compte is None:
        reponse = monde.client().get("/seances/999999/")
    else:
        reponse = monde.client(getattr(monde, compte)).get(f"/seances/{seance.pk}/")

    assert reponse.status_code == 404
    assert "Dupont" not in reponse.content.decode()


def test_une_seance_validee_n_offre_ni_retrait_ni_recherche(monde: Monde) -> None:
    seance = monde.seance_validee()

    reponse = monde.client().get(f"/seances/{seance.pk}/?q=Leroy")
    page = reponse.content.decode()

    assert "Validée" in page
    assert "Retirer" not in page
    assert 'role="search"' not in page
    assert reponse.context["resultats"] == []


# --- Recherche dans l'annuaire --------------------------------------------------------


def test_la_recherche_trouve_un_joueur_d_une_autre_categorie_avec_le_minimum(
    monde: Monde,
) -> None:
    seance = monde.seance(None, monde.dupont)

    reponse = monde.client().get(f"/seances/{seance.pk}/", {"q": " leRo "})

    resultats = reponse.context["resultats"]
    assert [ligne["pk"] for ligne in resultats] == [monde.leroy.pk]
    assert set(resultats[0]) == {"pk", "nom", "prenom", "categorie_reference__code"}
    assert "2009" not in reponse.content.decode()


def test_la_recherche_porte_aussi_sur_le_prenom(monde: Monde) -> None:
    seance = monde.seance()

    resultats = monde.client().get(f"/seances/{seance.pk}/", {"q": "noah"}).context["resultats"]

    assert [ligne["nom"] for ligne in resultats] == ["Leroy"]


def test_la_recherche_ecarte_les_participants_et_les_archives(monde: Monde) -> None:
    seance = monde.seance(None, monde.dupont)

    client = monde.client()

    assert client.get(f"/seances/{seance.pk}/", {"q": "Dupont"}).context["resultats"] == []
    assert client.get(f"/seances/{seance.pk}/", {"q": "Bernard"}).context["resultats"] == []
    page = client.get(f"/seances/{seance.pk}/", {"q": "Bernard"}).content.decode()
    assert "Aucun joueur de l’annuaire ne correspond à « Bernard »" in page


def test_la_recherche_est_limitee(monde: Monde) -> None:
    for numero in range(25):
        monde.joueur(f"Martin{numero:02d}", "Test", monde.u17)
    seance = monde.seance()

    reponse = monde.client().get(f"/seances/{seance.pk}/", {"q": "Martin"})

    assert len(reponse.context["resultats"]) == 20
    assert "Seuls les 20 premiers joueurs sont affichés" in reponse.content.decode()


# --- Ajout d'un participant -----------------------------------------------------------


def test_un_joueur_invite_s_ajoute_depuis_l_annuaire(monde: Monde) -> None:
    seance = monde.seance(None, monde.dupont)
    avant = seance.updated_at
    client = monde.client()

    reponse = client.post(
        f"/seances/{seance.pk}/participants/ajouter/", {"joueur": monde.leroy.pk, "q": "Lero"}
    )

    assert reponse.status_code == 302
    assert reponse["Location"] == f"/seances/{seance.pk}/?q=Lero"
    participation = Participation.objects.get(seance=seance, joueur=monde.leroy)
    assert participation.updated_by == monde.compte19
    seance.refresh_from_db()
    assert seance.updated_by == monde.compte19
    assert seance.updated_at > avant
    page = client.get(reponse["Location"]).content.decode()
    assert "Noah Leroy est ajouté à la séance." in page
    assert "Participants (2)" in page


def test_un_joueur_deja_present_n_est_pas_ajoute_deux_fois(monde: Monde) -> None:
    seance = monde.seance(None, monde.dupont)
    client = monde.client()

    reponse = client.post(
        f"/seances/{seance.pk}/participants/ajouter/", {"joueur": monde.dupont.pk}
    )

    assert reponse["Location"] == f"/seances/{seance.pk}/"
    assert Participation.objects.filter(seance=seance).count() == 1
    assert (
        "Hugo Dupont participe déjà à la séance."
        in client.get(reponse["Location"]).content.decode()
    )


@pytest.mark.parametrize("joueur", ["bernard", "999999", "abc", ""])
def test_a3_seul_un_joueur_actif_de_l_annuaire_peut_etre_ajoute(monde: Monde, joueur: str) -> None:
    seance = monde.seance()
    valeur = str(monde.bernard.pk) if joueur == "bernard" else joueur

    reponse = monde.client().post(f"/seances/{seance.pk}/participants/ajouter/", {"joueur": valeur})

    assert reponse.status_code == 404
    assert _nombres() == (1, 0)


def test_a3_l_autre_preparateur_n_ajoute_rien_a_ses_seances(monde: Monde) -> None:
    seance = monde.seance()

    reponse = monde.client(monde.compte17).post(
        f"/seances/{seance.pk}/participants/ajouter/", {"joueur": monde.leroy.pk}
    )

    assert reponse.status_code == 404
    assert _nombres() == (1, 0)


def test_a_une_seance_validee_un_joueur_ne_s_ajoute_qu_avec_ses_trois_rpe(monde: Monde) -> None:
    # PR 4.5 : une séance validée se corrige, participants compris (ADR-0008, US-06) ; jusqu'à
    # la PR 4.4, rien ne s'y ajoutait. Sans ses trois RPE, l'ajout reste refusé.
    seance = monde.seance_validee()
    client = monde.client()
    url = f"/seances/{seance.pk}/participants/ajouter/"

    reponse = client.post(url, {"joueur": monde.leroy.pk})

    assert reponse["Location"] == f"/seances/{seance.pk}/corriger/"
    assert Participation.objects.filter(seance=seance).count() == 1
    page = client.get(reponse["Location"]).content.decode()
    assert (
        "Pour ajouter Noah Leroy à une séance validée, saisissez ses trois RPE, de 0 à 10." in page
    )

    rpe = {"rpe_cardio": "6", "rpe_musculaire": "11", "rpe_teta": "4"}
    client.post(url, {"joueur": monde.leroy.pk, **rpe})
    assert Participation.objects.filter(seance=seance).count() == 1

    client.post(url, {"joueur": monde.leroy.pk, **rpe, "rpe_musculaire": "5"})
    ajoutee = Participation.objects.get(seance=seance, joueur=monde.leroy)
    assert (ajoutee.rpe_cardio, ajoutee.rpe_musculaire, ajoutee.rpe_teta) == (6, 5, 4)
    assert ajoutee.updated_by == monde.compte19
    seance.refresh_from_db()
    assert seance.statut == "validee"
    assert seance.updated_by == monde.compte19


# --- Retrait d'un absent --------------------------------------------------------------


def test_un_absent_se_retire_de_la_seance(monde: Monde) -> None:
    seance = monde.seance(None, monde.dupont, monde.abel)
    participation = Participation.objects.get(seance=seance, joueur=monde.dupont)
    client = monde.client()

    reponse = client.post(f"/seances/{seance.pk}/participations/{participation.pk}/retirer/")

    assert reponse["Location"] == f"/seances/{seance.pk}/"
    assert [p.joueur for p in Participation.objects.filter(seance=seance)] == [monde.abel]
    seance.refresh_from_db()
    assert seance.updated_by == monde.compte19
    assert (
        "Hugo Dupont est retiré de la séance." in client.get(reponse["Location"]).content.decode()
    )


def test_a3_une_participation_d_une_autre_seance_ne_se_retire_pas_par_celle_ci(
    monde: Monde,
) -> None:
    seance = monde.seance(None, monde.dupont)
    autre_u19 = monde.seance(None, monde.abel)
    seance_u17 = monde.seance(monde.u17, monde.leroy)
    client = monde.client()

    for autre in (autre_u19, seance_u17):
        participation = Participation.objects.get(seance=autre)
        reponse = client.post(f"/seances/{seance.pk}/participations/{participation.pk}/retirer/")
        assert reponse.status_code == 404
    assert _nombres() == (3, 3)


def test_a3_l_autre_preparateur_ne_retire_personne_de_ses_seances(monde: Monde) -> None:
    seance = monde.seance(None, monde.leroy)
    participation = Participation.objects.get()

    reponse = monde.client(monde.compte17).post(
        f"/seances/{seance.pk}/participations/{participation.pk}/retirer/"
    )

    assert reponse.status_code == 404
    assert _nombres() == (1, 1)


def test_le_dernier_participant_d_une_seance_validee_ne_se_retire_pas(monde: Monde) -> None:
    # PR 4.5 : un absent se retire d'une séance validée (test suivant) ; jusqu'à la PR 4.4,
    # personne ne s'en retirait. Le dernier reste : une séance validée vide n'a pas de sens.
    seance = monde.seance_validee()
    participation = Participation.objects.get(seance=seance)
    client = monde.client()

    reponse = client.post(f"/seances/{seance.pk}/participations/{participation.pk}/retirer/")

    assert reponse["Location"] == f"/seances/{seance.pk}/corriger/"
    assert Participation.objects.filter(seance=seance).count() == 1
    page = client.get(reponse["Location"]).content.decode()
    assert "Une séance validée garde au moins un participant" in page


def test_un_absent_se_retire_d_une_seance_validee_qui_reste_validee(monde: Monde) -> None:
    seance = monde.seance_validee()
    Participation.objects.create(
        seance=seance, joueur=monde.abel, rpe_cardio=3, rpe_musculaire=3, rpe_teta=3
    )
    participation = Participation.objects.get(seance=seance, joueur=monde.abel)

    reponse = monde.client().post(
        f"/seances/{seance.pk}/participations/{participation.pk}/retirer/"
    )

    assert reponse["Location"] == f"/seances/{seance.pk}/corriger/"
    assert [p.joueur for p in Participation.objects.filter(seance=seance)] == [monde.dupont]
    seance.refresh_from_db()
    assert seance.statut == "validee"
    assert seance.updated_by == monde.compte19


@pytest.mark.parametrize("action", ["participants/ajouter", "participations/1/retirer"])
def test_les_participants_ne_changent_jamais_par_une_simple_lecture(
    monde: Monde, action: str
) -> None:
    seance = monde.seance()

    assert monde.client().get(f"/seances/{seance.pk}/{action}/").status_code == 405
