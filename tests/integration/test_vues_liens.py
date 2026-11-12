"""Liens joueurs : génération, révocation, régénération par le préparateur (US-07, A3, A5, D4)."""

import datetime
import hashlib
import logging
import re

import pytest
from django.contrib.auth.models import User
from django.db import connection
from django.test import Client

from suivi.acces import liens_actifs
from suivi.models import Categorie, Joueur, LienJoueur, Preparateur

pytestmark = pytest.mark.django_db

NAISSANCE = datetime.date(2007, 3, 14)
ADRESSE = re.compile(r"/q/([A-Za-z0-9_-]{43})(?![A-Za-z0-9_-])")


class Monde:
    def __init__(self) -> None:
        self.u19 = Categorie.objects.create(code="U19", libelle="U19")
        self.u17 = Categorie.objects.create(code="U17", libelle="U17")
        self.compte19 = User.objects.create_user("p19")
        self.compte17 = User.objects.create_user("p17")
        self.prep19 = Preparateur.objects.create(user=self.compte19, categorie=self.u19)
        Preparateur.objects.create(user=self.compte17, categorie=self.u17)
        self.dupont = self.joueur("Dupont", "Hugo", self.u19)
        self.archive = self.joueur("Bernard", "Léo", self.u19, actif=False)
        self.leroy = self.joueur("Leroy", "Noah", self.u17)

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


def _generer(client: Client, joueur: Joueur):  # noqa: ANN202
    return client.post(f"/joueurs/{joueur.pk}/lien/generer/")


def _jeton(reponse) -> str:  # noqa: ANN001
    trouves = ADRESSE.findall(reponse.content.decode())
    assert len(set(trouves)) == 1
    return trouves[0]


def _colonnes_texte() -> list[tuple[str, str]]:
    with connection.cursor() as curseur:
        curseur.execute(
            """
            SELECT table_name, column_name FROM information_schema.columns
            WHERE table_schema = 'public'
              AND data_type IN ('text', 'character varying', 'json', 'jsonb', 'bytea')
            """
        )
        return curseur.fetchall()


def _tables_et_colonnes_contenant(valeur: str) -> list[str]:
    trouves = []
    with connection.cursor() as curseur:
        for table, colonne in _colonnes_texte():
            curseur.execute(
                f'SELECT count(*) FROM "{table}" WHERE "{colonne}"::text LIKE %s',  # noqa: S608
                [f"%{valeur}%"],
            )
            if curseur.fetchone()[0]:
                trouves.append(f"{table}.{colonne}")
    return trouves


# --- Génération ------------------------------------------------------------------------


def test_la_generation_affiche_le_lien_et_son_qr_code(monde: Monde) -> None:
    reponse = _generer(monde.client(), monde.dupont)

    assert reponse.status_code == 200
    page = reponse.content.decode()
    assert "Dupont" in page
    jeton = _jeton(reponse)
    assert f"http://testserver/q/{jeton}" in page
    assert 'src="data:image/svg+xml' in page


def test_a5_seule_l_empreinte_du_jeton_est_stockee(monde: Monde) -> None:
    jeton = _jeton(_generer(monde.client(), monde.dupont))

    lien = LienJoueur.objects.get(joueur=monde.dupont)
    assert lien.token_hash == hashlib.sha256(jeton.encode()).hexdigest()
    assert lien.revoked_at is None
    assert lien.created_by == monde.compte19


def test_a5_le_jeton_en_clair_ne_figure_dans_aucune_colonne_de_la_base(monde: Monde) -> None:
    client = monde.client()
    jeton = _jeton(_generer(client, monde.dupont))
    client.get("/joueurs/")

    assert _tables_et_colonnes_contenant(jeton) == []
    assert _tables_et_colonnes_contenant(jeton[:20]) == []


def test_le_jeton_n_est_pas_journalise(monde: Monde, caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.DEBUG):
        jeton = _jeton(_generer(monde.client(), monde.dupont))

    assert jeton not in caplog.text
    assert all(jeton not in str(enregistrement.args) for enregistrement in caplog.records)


def test_le_lien_n_est_affiche_qu_une_seule_fois(monde: Monde) -> None:
    client = monde.client()
    jeton = _jeton(_generer(client, monde.dupont))

    for chemin in ("/joueurs/", f"/joueurs/{monde.dupont.pk}/modifier/"):
        assert jeton not in client.get(chemin).content.decode()


def test_la_page_du_lien_n_est_pas_mise_en_cache(monde: Monde) -> None:
    reponse = _generer(monde.client(), monde.dupont)

    assert "no-store" in reponse["Cache-Control"]


def test_la_generation_n_accepte_que_le_post(monde: Monde) -> None:
    client = monde.client()

    assert client.get(f"/joueurs/{monde.dupont.pk}/lien/generer/").status_code == 405
    assert LienJoueur.objects.count() == 0


def test_a3_pas_de_lien_pour_un_joueur_d_une_autre_categorie(monde: Monde) -> None:
    reponse = _generer(monde.client(), monde.leroy)

    assert reponse.status_code == 404
    assert LienJoueur.objects.count() == 0


def test_a3_le_prepateur_d_une_autre_categorie_ne_revoque_pas_ce_lien(monde: Monde) -> None:
    _generer(monde.client(), monde.dupont)

    reponse = monde.client(monde.compte17).post(f"/joueurs/{monde.dupont.pk}/lien/revoquer/")

    assert reponse.status_code == 404
    assert LienJoueur.objects.get(joueur=monde.dupont).revoked_at is None


def test_pas_de_lien_pour_un_joueur_archive(monde: Monde) -> None:
    reponse = _generer(monde.client(), monde.archive)

    assert reponse.status_code in {302, 404}
    assert LienJoueur.objects.count() == 0


def test_la_generation_exige_le_jeton_csrf(monde: Monde) -> None:
    client = Client(enforce_csrf_checks=True)
    client.force_login(monde.compte19)

    reponse = client.post(f"/joueurs/{monde.dupont.pk}/lien/generer/")

    assert reponse.status_code == 403
    assert LienJoueur.objects.count() == 0


# --- Régénération et révocation --------------------------------------------------------


def test_la_regeneration_revoque_l_ancien_lien_et_en_cree_un_autre(monde: Monde) -> None:
    client = monde.client()
    premier = _jeton(_generer(client, monde.dupont))
    second = _jeton(_generer(client, monde.dupont))

    assert premier != second
    liens = {lien.token_hash: lien for lien in LienJoueur.objects.filter(joueur=monde.dupont)}
    assert len(liens) == 2
    assert liens[hashlib.sha256(premier.encode()).hexdigest()].revoked_at is not None
    assert liens[hashlib.sha256(second.encode()).hexdigest()].revoked_at is None


def test_la_revocation_ferme_le_lien_sans_en_creer_un_autre(monde: Monde) -> None:
    client = monde.client()
    _generer(client, monde.dupont)

    reponse = client.post(f"/joueurs/{monde.dupont.pk}/lien/revoquer/")

    assert reponse.status_code == 302
    assert LienJoueur.objects.get(joueur=monde.dupont).revoked_at is not None
    assert not liens_actifs(monde.prep19).exists()


def test_revoquer_sans_lien_actif_ne_casse_rien(monde: Monde) -> None:
    reponse = monde.client().post(f"/joueurs/{monde.dupont.pk}/lien/revoquer/")

    assert reponse.status_code == 302
    assert LienJoueur.objects.count() == 0


def test_la_liste_indique_quel_joueur_a_un_lien_actif(monde: Monde) -> None:
    client = monde.client()
    avant = client.get("/joueurs/").content.decode()
    _generer(client, monde.dupont)
    apres = client.get("/joueurs/").content.decode()

    assert "Générer le lien" in avant
    assert "Lien actif" in apres
    assert "Régénérer" in apres
    assert "Révoquer" in apres


# --- Archivage et effacement (D4) ------------------------------------------------------


def test_d4_l_archivage_revoque_le_lien(monde: Monde) -> None:
    client = monde.client()
    _generer(client, monde.dupont)

    client.post(f"/joueurs/{monde.dupont.pk}/archiver/")

    assert LienJoueur.objects.get(joueur=monde.dupont).revoked_at is not None
    assert not liens_actifs(monde.prep19).exists()


def test_d4_la_reactivation_ne_ressuscite_pas_le_lien(monde: Monde) -> None:
    client = monde.client()
    _generer(client, monde.dupont)
    client.post(f"/joueurs/{monde.dupont.pk}/archiver/")

    client.post(f"/joueurs/{monde.dupont.pk}/reactiver/")

    assert not liens_actifs(monde.prep19).exists()


def test_d4_l_effacement_supprime_les_liens_du_joueur(monde: Monde) -> None:
    client = monde.client()
    _generer(client, monde.dupont)
    _generer(client, monde.dupont)

    monde.dupont.delete()

    assert LienJoueur.objects.count() == 0


def test_liens_actifs_est_limite_a_la_categorie_du_preparateur(monde: Monde) -> None:
    _generer(monde.client(), monde.dupont)
    _generer(monde.client(monde.compte17), monde.leroy)

    assert [lien.joueur for lien in liens_actifs(monde.prep19)] == [monde.dupont]
