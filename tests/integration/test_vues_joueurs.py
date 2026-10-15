"""Gestion des joueurs de sa catégorie par le préparateur (US-15, A3, D1, ADR-0009)."""

import datetime

import pytest
from django.contrib.auth.models import User
from django.test import Client

from suivi.acces import annuaire, joueurs_suivis
from suivi.forms import JoueurForm
from suivi.models import Categorie, Joueur, Participation, Preparateur, Seance

pytestmark = pytest.mark.django_db

NAISSANCE = datetime.date(2007, 3, 14)


class Monde:
    """Deux catégories, leurs préparateurs, et un joueur U17 qui s'entraîne avec les U19."""

    def __init__(self) -> None:
        self.u19 = Categorie.objects.create(code="U19", libelle="U19")
        self.u17 = Categorie.objects.create(code="U17", libelle="U17")
        self.compte19 = User.objects.create_user("p19")
        self.compte17 = User.objects.create_user("p17")
        Preparateur.objects.create(user=self.compte19, categorie=self.u19)
        Preparateur.objects.create(user=self.compte17, categorie=self.u17)
        self.dupont = self.joueur("Dupont", "Hugo", self.u19)
        self.archive = self.joueur("Bernard", "Léo", self.u19, actif=False)
        self.leroy = self.joueur("Leroy", "Noah", self.u17)
        self.invite = self.joueur("Invite", "Tom", self.u17)
        seance = Seance.objects.create(
            categorie_organisatrice=self.u19, date=NAISSANCE, type="foot", duree_min=60
        )
        Participation.objects.create(seance=seance, joueur=self.invite)

    @staticmethod
    def joueur(nom: str, prenom: str, categorie: Categorie, actif: bool = True) -> Joueur:
        return Joueur.objects.create(
            nom=nom,
            prenom=prenom,
            date_naissance=NAISSANCE,
            categorie_reference=categorie,
            actif=actif,
        )

    def client(self, compte: User | None = None) -> Client:
        client = Client()
        client.force_login(compte or self.compte19)
        return client


@pytest.fixture
def monde() -> Monde:
    return Monde()


def _identite(nom: str = "Martin", prenom: str = "Lucas", naissance: str = "2008-05-02"):  # noqa: ANN202
    return {"nom": nom, "prenom": prenom, "date_naissance": naissance}


# --- Liste ---------------------------------------------------------------------------


def test_la_liste_montre_ses_joueurs_actifs_puis_archives(monde: Monde) -> None:
    reponse = monde.client().get("/joueurs/")

    assert reponse.status_code == 200
    assert reponse.context["actifs"] == [monde.dupont]
    assert reponse.context["archives"] == [monde.archive]
    page = reponse.content.decode()
    assert page.index("Dupont") < page.index("Joueurs archivés") < page.index("Bernard")


def test_a3_la_liste_ne_montre_aucun_joueur_d_une_autre_categorie(monde: Monde) -> None:
    page = monde.client().get("/joueurs/").content.decode()

    assert "Leroy" not in page
    # L'invité s'entraîne avec les U19, mais sa catégorie de référence reste U17.
    assert "Invite" not in page


def test_la_liste_est_triee_par_nom(monde: Monde) -> None:
    abel = monde.joueur("Abel", "Yanis", monde.u19)
    zidane = monde.joueur("Zidane", "Enzo", monde.u19)

    actifs = monde.client().get("/joueurs/").context["actifs"]

    assert actifs == [abel, monde.dupont, zidane]


def test_la_navigation_signale_la_rubrique_des_joueurs(monde: Monde) -> None:
    page = monde.client().get("/joueurs/").content.decode()

    assert '<a href="/joueurs/" aria-current="page">Joueurs</a>' in page


# --- Création ------------------------------------------------------------------------


def test_un_joueur_cree_appartient_a_la_categorie_du_preparateur(monde: Monde) -> None:
    client = monde.client()

    reponse = client.post("/joueurs/nouveau/", _identite())

    assert reponse.status_code == 302
    assert reponse["Location"] == "/joueurs/"
    joueur = Joueur.objects.get(nom="Martin")
    assert joueur.prenom == "Lucas"
    assert joueur.date_naissance == datetime.date(2008, 5, 2)
    assert joueur.categorie_reference == monde.u19
    assert joueur.actif is True
    assert joueur.updated_by == monde.compte19
    assert "Lucas Martin est ajouté à la catégorie." in client.get("/joueurs/").content.decode()


def test_a3_la_categorie_et_l_archivage_ne_se_choisissent_pas_dans_la_requete(
    monde: Monde,
) -> None:
    donnees = {**_identite(), "categorie_reference": monde.u17.pk, "actif": ""}

    monde.client().post("/joueurs/nouveau/", donnees)

    joueur = Joueur.objects.get(nom="Martin")
    assert joueur.categorie_reference == monde.u19
    assert joueur.actif is True


def test_le_formulaire_de_creation_s_affiche_vide(monde: Monde) -> None:
    reponse = monde.client().get("/joueurs/nouveau/")
    page = reponse.content.decode()

    assert reponse.status_code == 200
    assert "<h1>Ajouter un joueur</h1>" in page
    assert 'type="date"' in page
    assert "Prénom" in page


# --- D1 : saisies refusées, à la saisie comme en base ---------------------------------


@pytest.mark.parametrize(
    ("donnees", "champ"),
    [
        (_identite(nom="   "), "nom"),
        (_identite(prenom=""), "prenom"),
        (_identite(nom="x" * 101), "nom"),
        (_identite(naissance="2007-02-30"), "date_naissance"),
        (_identite(naissance=""), "date_naissance"),
        (_identite(naissance="2999-01-01"), "date_naissance"),
    ],
    ids=["nom-blanc", "prenom-vide", "nom-trop-long", "date-impossible", "date-vide", "futur"],
)
def test_d1_une_saisie_invalide_est_refusee_sans_rien_enregistrer(
    monde: Monde, donnees: dict[str, str], champ: str
) -> None:
    avant = Joueur.objects.count()

    reponse = monde.client().post("/joueurs/nouveau/", donnees)

    assert reponse.status_code == 200
    assert reponse.context["form"].errors[champ]
    assert '<small class="erreur">' in reponse.content.decode()
    assert Joueur.objects.count() == avant


@pytest.mark.parametrize(
    ("naissance", "valide"),
    [("2026-10-14", True), ("2026-10-15", True), ("2026-10-16", False)],
)
def test_d1_la_date_de_naissance_va_au_plus_jusqu_a_aujourd_hui(
    monkeypatch: pytest.MonkeyPatch, naissance: str, valide: bool
) -> None:
    monkeypatch.setattr("suivi.forms.aujourd_hui", lambda: datetime.date(2026, 10, 15))

    form = JoueurForm(_identite(naissance=naissance))

    assert form.is_valid() is valide
    if not valide:
        assert form.errors["date_naissance"] == [
            "La date de naissance ne peut pas être dans le futur."
        ]


# --- Modification --------------------------------------------------------------------


def test_le_formulaire_de_modification_est_pre_rempli(monde: Monde) -> None:
    page = monde.client().get(f"/joueurs/{monde.dupont.pk}/modifier/").content.decode()

    assert "<h1>Modifier Hugo Dupont</h1>" in page
    assert 'value="Dupont"' in page
    assert 'value="2007-03-14"' in page


def test_une_modification_est_enregistree_avec_son_auteur(monde: Monde) -> None:
    avant = monde.dupont.updated_at

    reponse = monde.client().post(
        f"/joueurs/{monde.dupont.pk}/modifier/", _identite("Dupond", "Hugo", "2007-03-15")
    )

    assert reponse["Location"] == "/joueurs/"
    monde.dupont.refresh_from_db()
    assert (monde.dupont.nom, monde.dupont.date_naissance) == ("Dupond", datetime.date(2007, 3, 15))
    assert monde.dupont.categorie_reference == monde.u19
    assert monde.dupont.updated_by == monde.compte19
    assert monde.dupont.updated_at > avant


def test_un_joueur_archive_se_modifie_et_reste_archive(monde: Monde) -> None:
    monde.client().post(f"/joueurs/{monde.archive.pk}/modifier/", _identite("Bernard", "Léon"))

    monde.archive.refresh_from_db()
    assert monde.archive.prenom == "Léon"
    assert monde.archive.actif is False


# --- Archivage et réactivation (ADR-0009) --------------------------------------------


def test_l_archivage_retire_le_joueur_de_l_annuaire_et_garde_son_historique(
    monde: Monde,
) -> None:
    preparateur = Preparateur.objects.get(user=monde.compte19)
    client = monde.client()

    reponse = client.post(f"/joueurs/{monde.dupont.pk}/archiver/")

    assert reponse["Location"] == "/joueurs/"
    monde.dupont.refresh_from_db()
    assert monde.dupont.actif is False
    assert monde.dupont.updated_by == monde.compte19
    assert monde.dupont.pk not in {ligne["pk"] for ligne in annuaire(preparateur)}
    assert monde.dupont in joueurs_suivis(preparateur)
    page = client.get("/joueurs/").content.decode()
    assert "Hugo Dupont est archivé" in page
    assert page.index("Joueurs archivés") < page.index("<strong>Dupont</strong>")


def test_la_reactivation_remet_le_joueur_dans_les_listes(monde: Monde) -> None:
    preparateur = Preparateur.objects.get(user=monde.compte19)

    monde.client().post(f"/joueurs/{monde.archive.pk}/reactiver/")

    monde.archive.refresh_from_db()
    assert monde.archive.actif is True
    assert monde.archive.updated_by == monde.compte19
    assert monde.archive.pk in {ligne["pk"] for ligne in annuaire(preparateur)}


@pytest.mark.parametrize("action", ["archiver", "reactiver"])
def test_l_archivage_ne_se_fait_jamais_par_une_simple_lecture(monde: Monde, action: str) -> None:
    reponse = monde.client().get(f"/joueurs/{monde.dupont.pk}/{action}/")

    assert reponse.status_code == 405
    monde.dupont.refresh_from_db()
    assert monde.dupont.actif is True


# --- A3 : un joueur d'une autre catégorie est introuvable ------------------------------


@pytest.mark.parametrize("cible", ["leroy", "invite"])
@pytest.mark.parametrize(
    ("methode", "action", "donnees"),
    [
        ("get", "modifier", None),
        ("post", "modifier", _identite("Pirate", "Pirate")),
        ("post", "archiver", None),
        ("post", "reactiver", None),
    ],
)
def test_a3_un_joueur_d_une_autre_categorie_ne_se_lit_ni_ne_se_modifie(
    monde: Monde, cible: str, methode: str, action: str, donnees: dict[str, str] | None
) -> None:
    joueur: Joueur = getattr(monde, cible)
    avant = Joueur.objects.values().get(pk=joueur.pk)

    reponse = getattr(monde.client(), methode)(f"/joueurs/{joueur.pk}/{action}/", donnees or {})

    assert reponse.status_code == 404
    assert joueur.nom not in reponse.content.decode()
    assert Joueur.objects.values().get(pk=joueur.pk) == avant


def test_a3_un_joueur_inexistant_donne_la_meme_reponse(monde: Monde) -> None:
    assert monde.client().get("/joueurs/999999/modifier/").status_code == 404


def test_a3_l_autre_preparateur_gere_ses_propres_joueurs(monde: Monde) -> None:
    client = monde.client(monde.compte17)

    assert set(client.get("/joueurs/").context["actifs"]) == {monde.invite, monde.leroy}
    assert client.get(f"/joueurs/{monde.dupont.pk}/modifier/").status_code == 404
    assert client.post(f"/joueurs/{monde.leroy.pk}/archiver/").status_code == 302
