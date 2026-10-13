"""Accès du staff : profil préparateur exigé (A1 connecté), périmètre (A3), inscription (A6)."""

import datetime

import pytest
from catalogue_acces import catalogue_des_routes, routes_qui_fuient
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import get_resolver

from suivi.acces import (
    annuaire,
    entrees_visibles,
    joueurs_suivis,
    participations_visibles,
    seances_organisees,
)
from suivi.models import (
    Categorie,
    EntreeSensations,
    Joueur,
    Participation,
    Preparateur,
    Seance,
)

pytestmark = pytest.mark.django_db(transaction=True)

JOUR = datetime.date(2026, 10, 12)
NAISSANCE = datetime.date(2007, 3, 14)


def _client(compte: object) -> Client:
    client = Client()
    client.force_login(compte)  # type: ignore[arg-type]
    return client


# --- A1 : un compte connecté sans profil préparateur ---------------------------------


def test_a1_un_compte_sans_profil_n_entre_sur_aucune_route_staff() -> None:
    compte = get_user_model().objects.create_user("sans_profil")
    # La déconnexion de l'administration est ouverte à tout compte connecté : elle ne
    # montre aucune donnée et ne fait que clore la session.
    chemins = [c for c in catalogue_des_routes() if c != "/admin/logout/"]
    assert routes_qui_fuient(_client(compte), chemins) == []


def test_a1_un_superutilisateur_sans_profil_n_entre_pas_sur_les_pages_staff() -> None:
    admin = get_user_model().objects.create_superuser("admin")
    assert _client(admin).get("/").status_code == 403


def test_a1_un_preparateur_entre_sur_les_pages_staff() -> None:
    u19 = Categorie.objects.create(code="U19", libelle="U19")
    compte = get_user_model().objects.create_user("prep")
    Preparateur.objects.create(user=compte, categorie=u19)
    assert _client(compte).get("/").status_code == 200


def test_a1_la_liste_blanche_reste_ouverte_a_un_compte_sans_profil() -> None:
    compte = get_user_model().objects.create_user("sans_profil")
    client = _client(compte)
    assert client.get("/sante/").status_code == 200
    assert client.get("/connexion/").status_code in {200, 302}


# --- Administration réservée au superutilisateur ------------------------------------


def test_un_preparateur_meme_marque_is_staff_n_entre_pas_dans_l_administration() -> None:
    u19 = Categorie.objects.create(code="U19", libelle="U19")
    compte = get_user_model().objects.create_user("prep", is_staff=True)
    Preparateur.objects.create(user=compte, categorie=u19)
    client = _client(compte)
    for chemin in ("/admin/", "/admin/suivi/joueur/", "/admin/auth/user/"):
        reponse = client.get(chemin)
        assert reponse.status_code == 302
        assert "/admin/login/" in reponse["Location"]


def test_le_superutilisateur_entre_dans_l_administration() -> None:
    admin = get_user_model().objects.create_superuser("admin")
    assert _client(admin).get("/admin/").status_code == 200


# --- A6 : aucune inscription publique ------------------------------------------------


def test_a6_aucune_route_d_inscription() -> None:
    chemins = [c for c in catalogue_des_routes()] + ["/connexion/", "/sante/", "/admin/login/"]
    mots = ("inscri", "register", "signup", "creer-compte", "password_reset", "mot-de-passe")
    assert [c for c in chemins if any(m in c.lower() for m in mots)] == []
    assert get_resolver().resolve("/") is not None


@pytest.mark.parametrize("chemin", ["/admin/auth/user/add/", "/connexion/", "/"])
def test_a6_un_visiteur_ne_cree_aucun_compte(chemin: str) -> None:
    donnees = {"username": "intrus", "password1": "x", "password2": "x", "password": "x"}
    Client().post(chemin, donnees)
    assert not get_user_model().objects.filter(username="intrus").exists()


def test_a6_un_preparateur_ne_cree_aucun_compte() -> None:
    u19 = Categorie.objects.create(code="U19", libelle="U19")
    compte = get_user_model().objects.create_user("prep", is_staff=True)
    Preparateur.objects.create(user=compte, categorie=u19)
    reponse = _client(compte).post(
        "/admin/auth/user/add/",
        {"username": "intrus", "password1": "Motdepasse-123", "password2": "Motdepasse-123"},
    )
    assert reponse.status_code == 302
    assert not get_user_model().objects.filter(username="intrus").exists()


def test_a6_le_superutilisateur_peut_creer_un_compte() -> None:
    admin = get_user_model().objects.create_superuser("admin")
    reponse = _client(admin).post(
        "/admin/auth/user/add/",
        {"username": "nouveau", "password1": "Motdepasse-123", "password2": "Motdepasse-123"},
    )
    assert reponse.status_code == 302
    assert get_user_model().objects.filter(username="nouveau").exists()


# --- A3 : deux catégories, deux préparateurs, un joueur invité -----------------------


@pytest.fixture
def monde() -> dict[str, object]:
    u19 = Categorie.objects.create(code="U19", libelle="U19")
    u17 = Categorie.objects.create(code="U17", libelle="U17")
    utilisateur = get_user_model().objects
    prep19 = Preparateur.objects.create(user=utilisateur.create_user("p19"), categorie=u19)
    prep17 = Preparateur.objects.create(user=utilisateur.create_user("p17"), categorie=u17)

    def joueur(nom: str, categorie: Categorie, actif: bool = True) -> Joueur:
        return Joueur.objects.create(
            nom=nom,
            prenom="Test",
            date_naissance=NAISSANCE,
            categorie_reference=categorie,
            actif=actif,
        )

    j19 = joueur("Dupont", u19)
    archive19 = joueur("Archive", u19, actif=False)
    j17 = joueur("Leroy", u17)
    invite = joueur("Invite", u17)  # catégorie de référence U17, s'entraîne avec les U19
    s19 = Seance.objects.create(categorie_organisatrice=u19, date=JOUR, type="foot", duree_min=90)
    s17 = Seance.objects.create(categorie_organisatrice=u17, date=JOUR, type="foot", duree_min=60)
    p = {
        "j19_s19": Participation.objects.create(seance=s19, joueur=j19),
        "invite_s19": Participation.objects.create(seance=s19, joueur=invite),
        "j17_s17": Participation.objects.create(seance=s17, joueur=j17),
        "invite_s17": Participation.objects.create(seance=s17, joueur=invite),
    }
    e = {
        "j19": EntreeSensations.objects.create(joueur=j19, date=JOUR),
        "j17": EntreeSensations.objects.create(joueur=j17, date=JOUR),
        "invite": EntreeSensations.objects.create(joueur=invite, date=JOUR),
    }
    return {
        "prep19": prep19,
        "prep17": prep17,
        "j19": j19,
        "archive19": archive19,
        "j17": j17,
        "invite": invite,
        "s19": s19,
        "s17": s17,
        "p": p,
        "e": e,
    }


def test_a3_joueurs_suivis_limites_a_la_categorie_de_reference(monde: dict[str, object]) -> None:
    assert set(joueurs_suivis(monde["prep19"])) == {monde["j19"], monde["archive19"]}  # type: ignore[arg-type]
    assert set(joueurs_suivis(monde["prep17"])) == {monde["j17"], monde["invite"]}  # type: ignore[arg-type]


def test_a3_annuaire_minimal_des_joueurs_actifs_de_toutes_les_categories(
    monde: dict[str, object],
) -> None:
    lignes = list(annuaire(monde["prep19"]))  # type: ignore[arg-type]
    assert {ligne["nom"] for ligne in lignes} == {"Dupont", "Leroy", "Invite"}
    for ligne in lignes:
        assert set(ligne) == {"pk", "nom", "prenom", "categorie_reference__code"}
    assert {ligne["categorie_reference__code"] for ligne in lignes} == {"U19", "U17"}


def test_a3_seances_organisees_limitees_a_la_categorie(monde: dict[str, object]) -> None:
    assert set(seances_organisees(monde["prep19"])) == {monde["s19"]}  # type: ignore[arg-type]
    assert set(seances_organisees(monde["prep17"])) == {monde["s17"]}  # type: ignore[arg-type]


def test_a3_participations_de_ses_joueurs_et_de_l_invite_a_ses_seances(
    monde: dict[str, object],
) -> None:
    p = monde["p"]
    assert set(participations_visibles(monde["prep19"])) == {  # type: ignore[arg-type]
        p["j19_s19"],  # type: ignore[index]
        p["invite_s19"],  # type: ignore[index]
    }
    assert set(participations_visibles(monde["prep17"])) == {  # type: ignore[arg-type]
        p["j17_s17"],  # type: ignore[index]
        p["invite_s17"],  # type: ignore[index]
        p["invite_s19"],  # type: ignore[index]
    }


def test_a3_le_preparateur_organisateur_ne_voit_pas_l_historique_de_l_invite(
    monde: dict[str, object],
) -> None:
    visibles = participations_visibles(monde["prep19"])  # type: ignore[arg-type]
    assert not visibles.filter(seance=monde["s17"]).exists()  # type: ignore[misc]


def test_a3_entrees_de_sensations_limitees_aux_joueurs_suivis(monde: dict[str, object]) -> None:
    e = monde["e"]
    assert set(entrees_visibles(monde["prep19"])) == {e["j19"]}  # type: ignore[arg-type,index]
    assert set(entrees_visibles(monde["prep17"])) == {e["j17"], e["invite"]}  # type: ignore[arg-type,index]
