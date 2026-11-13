"""Questionnaire du jour par le lien du joueur (US-08, US-09, A4, A5, D1, D2, D4)."""

import datetime
import logging
import re

import pytest
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.test import Client
from django.urls import reverse

from suivi.liens import archiver_joueur, creer_lien
from suivi.models import (
    Categorie,
    EntreeSensations,
    Indicateur,
    Joueur,
    LienJoueur,
    Preparateur,
    Reponse,
)

pytestmark = pytest.mark.django_db

NAISSANCE = datetime.date(2007, 3, 14)
JOUR = datetime.date(2026, 11, 13)
VEILLE = datetime.date(2026, 11, 12)
LENDEMAIN = datetime.date(2026, 11, 14)
JETON_JAMAIS_EMIS = "J" * 43


class Monde:
    def __init__(self) -> None:
        self.u19 = Categorie.objects.create(code="U19", libelle="U19")
        self.u17 = Categorie.objects.create(code="U17", libelle="U17")
        self.compte = User.objects.create_user("p19")
        Preparateur.objects.create(user=self.compte, categorie=self.u19)
        self.fatigue = self.note(self.u19, "fatigue", "Fatigue", ordre=1)
        self.plaisir = self.note(self.u19, "plaisir", "Plaisir", ordre=2)
        self.coucher = Indicateur.objects.create(
            categorie=self.u19,
            code="heure_coucher",
            libelle="Heure de coucher",
            type="heure",
            borne_min=0,
            borne_max=1439,
            sens="aucun",
            poids=0,
            inclus_score=False,
            ordre=3,
        )
        self.ancien = self.note(self.u19, "ancien", "Indicateur retiré", ordre=4, actif=False)
        self.autre_categorie = self.note(self.u17, "concentration", "Concentration U17")
        self.dupont = self.joueur("Dupont", "Hugo", self.u19)
        self.petit = self.joueur("Petit", "Noé", self.u19)
        self.leroy = self.joueur("Leroy", "Noah", self.u17)
        self.jeton = creer_lien(self.dupont, self.compte)

    @staticmethod
    def note(
        categorie: Categorie, code: str, libelle: str, ordre: int = 0, actif: bool = True
    ) -> Indicateur:
        return Indicateur.objects.create(
            categorie=categorie,
            code=code,
            libelle=libelle,
            type="note",
            borne_min=0,
            borne_max=10,
            sens="bas_bon",
            ordre=ordre,
            actif=actif,
        )

    @staticmethod
    def joueur(nom: str, prenom: str, categorie: Categorie) -> Joueur:
        return Joueur.objects.create(
            nom=nom, prenom=prenom, date_naissance=NAISSANCE, categorie_reference=categorie
        )

    def saisie(self, **valeurs: str) -> dict[str, str]:
        """Champs d'une réponse complète, remplacés par `valeurs` (clé : code de l'indicateur)."""
        complete = {"fatigue": "4", "plaisir": "8", "heure_coucher": "23:30"}
        complete.update(valeurs)
        champs = {"date": JOUR.isoformat()}
        for code, valeur in complete.items():
            champs[f"i{Indicateur.objects.get(code=code, categorie=self.u19).pk}"] = valeur
        return champs

    def chemin(self, jeton: str | None = None) -> str:
        return f"/q/{jeton or self.jeton}"


@pytest.fixture
def monde(monkeypatch: pytest.MonkeyPatch) -> Monde:
    monkeypatch.setattr("suivi.views.questionnaire.aujourd_hui", lambda: JOUR)
    return Monde()


def _enregistre(monde: Monde, joueur: Joueur | None = None, jour: datetime.date = JOUR) -> dict:
    return {
        reponse.indicateur.code: reponse.valeur
        for reponse in Reponse.objects.filter(
            entree__joueur=joueur or monde.dupont, entree__date=jour
        ).select_related("indicateur")
    }


# --- Affichage -------------------------------------------------------------------------


def test_la_page_propose_les_indicateurs_actifs_de_la_categorie_de_reference(
    monde: Monde,
) -> None:
    reponse = Client().get(monde.chemin())

    page = reponse.content.decode()
    assert reponse.status_code == 200
    assert "Hugo" in page
    for libelle in ("Fatigue", "Plaisir", "Heure de coucher"):
        assert libelle in page
    assert "Indicateur retiré" not in page
    assert "Concentration U17" not in page
    assert 'type="time"' in page
    assert page.index("Fatigue") < page.index("Plaisir") < page.index("Heure de coucher")


def test_la_page_ne_montre_ni_autre_joueur_ni_navigation_du_staff(monde: Monde) -> None:
    page = Client().get(monde.chemin()).content.decode()

    assert "Petit" not in page
    assert "Leroy" not in page
    assert "/joueurs/" not in page
    assert "/seances/" not in page


def test_la_page_porte_les_en_tetes_du_lien_joueur(monde: Monde) -> None:
    reponse = Client().get(monde.chemin())

    # `same-origin` : `no-referrer` ferait refuser le formulaire par le contrôle CSRF.
    assert reponse["Referrer-Policy"] == "same-origin"
    assert reponse["X-Frame-Options"] == "DENY"
    assert "no-store" in reponse["Cache-Control"]
    assert "default-src 'self'" in reponse["Content-Security-Policy"]


def test_la_page_ne_cree_aucune_session(monde: Monde) -> None:
    Client().get(monde.chemin())

    assert Session.objects.count() == 0


def test_l_adresse_se_construit_par_reverse() -> None:
    assert reverse("questionnaire", kwargs={"jeton": "abc"}) == "/q/abc"


def test_seule_la_lecture_et_l_envoi_sont_acceptes(monde: Monde) -> None:
    client = Client()

    assert client.put(monde.chemin()).status_code == 405
    assert client.delete(monde.chemin()).status_code == 405


# --- Création et modification (US-08, US-09, D2) ---------------------------------------


def test_un_premier_envoi_cree_l_entree_du_jour(monde: Monde) -> None:
    reponse = Client().post(monde.chemin(), monde.saisie())

    assert reponse.status_code == 200
    assert "enregistré" in reponse.content.decode()
    assert _enregistre(monde) == {"fatigue": 4, "plaisir": 8, "heure_coucher": 23 * 60 + 30}
    entree = EntreeSensations.objects.get(joueur=monde.dupont)
    assert entree.date == JOUR
    # Nul quand l'auteur est le joueur passant par son lien (ADR-0008).
    assert entree.updated_by is None


def test_d2_un_second_envoi_modifie_l_entree_sans_en_creer_une_autre(monde: Monde) -> None:
    client = Client()
    client.post(monde.chemin(), monde.saisie())
    premiere_modification = EntreeSensations.objects.get().updated_at

    reponse = client.post(monde.chemin(), monde.saisie(fatigue="9", heure_coucher="00:15"))

    assert reponse.status_code == 200
    assert EntreeSensations.objects.filter(joueur=monde.dupont).count() == 1
    assert EntreeSensations.objects.get().updated_at > premiere_modification
    assert Reponse.objects.filter(entree__joueur=monde.dupont).count() == 3
    assert _enregistre(monde) == {"fatigue": 9, "plaisir": 8, "heure_coucher": 15}


def test_rouvrir_le_lien_le_meme_jour_preremplit_les_reponses(monde: Monde) -> None:
    Client().post(monde.chemin(), monde.saisie())

    page = Client().get(monde.chemin()).content.decode()

    assert 'value="4"' in page
    assert 'value="8"' in page
    assert 'value="23:30"' in page


def test_la_modification_garde_les_reponses_d_un_indicateur_desactive(monde: Monde) -> None:
    entree = EntreeSensations.objects.create(joueur=monde.dupont, date=JOUR)
    Reponse.objects.create(entree=entree, indicateur=monde.ancien, valeur=6)

    Client().post(monde.chemin(), monde.saisie())

    assert _enregistre(monde)["ancien"] == 6  # ADR-0016 : jamais supprimée


def test_l_envoi_ne_peut_viser_ni_un_autre_joueur_ni_un_autre_jour_ni_une_autre_categorie(
    monde: Monde,
) -> None:
    champs = monde.saisie()
    champs.update(
        joueur=str(monde.petit.pk),
        joueur_id=str(monde.petit.pk),
        updated_by="1",
        **{f"i{monde.autre_categorie.pk}": "5", f"i{monde.ancien.pk}": "5"},
    )

    Client().post(monde.chemin(), champs)

    assert EntreeSensations.objects.get().joueur == monde.dupont
    assert set(_enregistre(monde)) == {"fatigue", "plaisir", "heure_coucher"}


# --- A4 : le lien ne voit que le jour même ---------------------------------------------


def test_a4_le_lien_ne_lit_ni_une_entree_passee_ni_un_autre_joueur(monde: Monde) -> None:
    veille = EntreeSensations.objects.create(joueur=monde.dupont, date=VEILLE)
    Reponse.objects.create(entree=veille, indicateur=monde.fatigue, valeur=7)
    autre = EntreeSensations.objects.create(joueur=monde.petit, date=JOUR)
    Reponse.objects.create(entree=autre, indicateur=monde.fatigue, valeur=3)

    page = Client().get(monde.chemin()).content.decode()

    assert not re.search(r'value="[37]"', page)
    assert 'value="23:30"' not in page


def test_a4_un_envoi_ne_touche_pas_une_entree_passee_ni_celle_d_un_autre(monde: Monde) -> None:
    veille = EntreeSensations.objects.create(joueur=monde.dupont, date=VEILLE)
    Reponse.objects.create(entree=veille, indicateur=monde.fatigue, valeur=7)
    autre = EntreeSensations.objects.create(joueur=monde.petit, date=JOUR)
    Reponse.objects.create(entree=autre, indicateur=monde.fatigue, valeur=3)

    Client().post(monde.chemin(), monde.saisie())

    assert _enregistre(monde, monde.dupont, VEILLE) == {"fatigue": 7}
    assert _enregistre(monde, monde.petit) == {"fatigue": 3}


def test_a4_aucune_autre_route_n_accepte_le_jeton(monde: Monde) -> None:
    client = Client()
    jeton = monde.jeton
    chemins = [
        f"/q/{jeton}/",
        f"/q/{jeton}/autre",
        f"/joueurs/{jeton}/",
        f"/seances/{jeton}/",
        f"/?jeton={jeton}",
        f"/sante/?jeton={jeton}",
        f"/connexion/?next=/q/{jeton}",
    ]
    for chemin in chemins:
        reponse = client.get(chemin)
        page = reponse.content.decode()
        assert "Fatigue" not in page, chemin
        assert "Hugo" not in page, chemin
    assert client.get(f"/q/{jeton}/").status_code == 404


def test_a4_la_route_n_exige_pas_de_session_et_ne_redirige_pas(monde: Monde) -> None:
    # Une redirection vers la connexion placerait le jeton dans l'adresse `?next=`.
    reponse = Client().get(monde.chemin())

    assert reponse.status_code == 200
    assert not reponse.has_header("Location")


# --- A5 : même 404 pour un lien invalide, révoqué ou régénéré --------------------------


def _404(client: Client, chemin: str, methode: str) -> tuple[int, bytes]:
    reponse = getattr(client, methode)(chemin)
    return reponse.status_code, reponse.content


@pytest.mark.parametrize("methode", ["get", "post"])
def test_a5_un_lien_invalide_revoque_ou_regenere_donne_le_meme_404(
    monde: Monde, methode: str
) -> None:
    ancien = monde.jeton
    nouveau = creer_lien(monde.dupont, monde.compte)  # régénère : l'ancien est révoqué
    revoque = creer_lien(monde.petit, monde.compte)
    LienJoueur.objects.filter(joueur=monde.petit).update(
        revoked_at=datetime.datetime.now(datetime.UTC)
    )
    client = Client()

    invalide = _404(client, monde.chemin(JETON_JAMAIS_EMIS), methode)
    regenere = _404(client, monde.chemin(ancien), methode)
    revoque_resultat = _404(client, monde.chemin(revoque), methode)

    assert invalide[0] == 404
    assert invalide == regenere == revoque_resultat
    assert Client().get(monde.chemin(nouveau)).status_code == 200


def test_a5_un_refus_n_ecrit_rien(monde: Monde) -> None:
    Client().post(monde.chemin(JETON_JAMAIS_EMIS), monde.saisie())

    assert EntreeSensations.objects.count() == 0


def test_a5_le_jeton_n_est_pas_journalise_meme_quand_le_lien_est_refuse(
    monde: Monde, caplog: pytest.LogCaptureFixture
) -> None:
    ancien = monde.jeton
    creer_lien(monde.dupont, monde.compte)

    with caplog.at_level(logging.DEBUG):
        Client().get(monde.chemin(ancien))
        Client().post(monde.chemin(JETON_JAMAIS_EMIS), monde.saisie())

    assert caplog.records, "le refus 404 doit être journalisé, sans le jeton"
    for jeton in (ancien, JETON_JAMAIS_EMIS):
        assert jeton not in caplog.text
        assert all(jeton not in str(enregistrement.args) for enregistrement in caplog.records)


# --- D4 : archivage et effacement ------------------------------------------------------


def test_d4_un_joueur_archive_n_ouvre_plus_son_lien(monde: Monde) -> None:
    archiver_joueur(monde.dupont, monde.compte)

    assert Client().get(monde.chemin()).status_code == 404
    assert Client().post(monde.chemin(), monde.saisie()).status_code == 404
    assert EntreeSensations.objects.count() == 0


def test_d4_un_joueur_inactif_dont_le_lien_serait_actif_est_refuse(monde: Monde) -> None:
    # Défense en profondeur : l'archivage révoque le lien, mais la vue ne s'y fie pas.
    Joueur.objects.filter(pk=monde.dupont.pk).update(actif=False)

    assert LienJoueur.objects.filter(joueur=monde.dupont, revoked_at__isnull=True).exists()
    assert Client().get(monde.chemin()).status_code == 404
    assert Client().post(monde.chemin(), monde.saisie()).status_code == 404


def test_d4_un_joueur_efface_n_ouvre_plus_son_lien(monde: Monde) -> None:
    monde.dupont.delete()

    assert Client().get(monde.chemin()).status_code == 404


# --- D1 : valeurs hors plage -----------------------------------------------------------


@pytest.mark.parametrize(
    "valeurs",
    [
        {"fatigue": "11"},
        {"fatigue": "-1"},
        {"fatigue": "4.5"},
        {"fatigue": "beaucoup"},
        {"fatigue": ""},
        {"heure_coucher": "24:00"},
        {"heure_coucher": "tard"},
        {"heure_coucher": ""},
    ],
    ids=lambda v: "=".join(next(iter(v.items()))),
)
def test_d1_une_valeur_hors_echelle_est_refusee_sans_rien_enregistrer(
    monde: Monde, valeurs: dict[str, str]
) -> None:
    reponse = Client().post(monde.chemin(), monde.saisie(**valeurs))

    assert reponse.status_code == 200
    assert 'class="erreur"' in reponse.content.decode()
    assert EntreeSensations.objects.count() == 0
    assert Reponse.objects.count() == 0


def test_d1_un_champ_absent_est_refuse(monde: Monde) -> None:
    champs = monde.saisie()
    del champs[f"i{monde.plaisir.pk}"]

    reponse = Client().post(monde.chemin(), champs)

    assert 'class="erreur"' in reponse.content.decode()
    assert EntreeSensations.objects.count() == 0


def test_d1_les_bornes_sont_acceptees(monde: Monde) -> None:
    Client().post(monde.chemin(), monde.saisie(fatigue="0", plaisir="10", heure_coucher="23:59"))

    assert _enregistre(monde) == {"fatigue": 0, "plaisir": 10, "heure_coucher": 1439}


def test_d1_une_erreur_garde_les_autres_reponses_dans_le_formulaire(monde: Monde) -> None:
    page = Client().post(monde.chemin(), monde.saisie(fatigue="11")).content.decode()

    assert 'value="8"' in page


# --- Minuit : l'entrée du jour est celle du jour de la page ----------------------------


def test_un_envoi_apres_minuit_ne_s_enregistre_pas_sur_le_nouveau_jour(
    monde: Monde, monkeypatch: pytest.MonkeyPatch
) -> None:
    client = Client()
    page = client.get(monde.chemin())  # chargée un jour J
    assert f'value="{JOUR.isoformat()}"' in page.content.decode()
    monkeypatch.setattr("suivi.views.questionnaire.aujourd_hui", lambda: LENDEMAIN)

    reponse = client.post(monde.chemin(), monde.saisie())

    assert reponse.status_code == 200
    assert EntreeSensations.objects.count() == 0
    assert "nouvelle journée" in reponse.content.decode()
    assert f'value="{LENDEMAIN.isoformat()}"' in reponse.content.decode()


def test_le_lendemain_le_formulaire_est_vide_et_l_entree_de_la_veille_intacte(
    monde: Monde, monkeypatch: pytest.MonkeyPatch
) -> None:
    Client().post(monde.chemin(), monde.saisie())
    monkeypatch.setattr("suivi.views.questionnaire.aujourd_hui", lambda: LENDEMAIN)

    page = Client().get(monde.chemin()).content.decode()
    Client().post(monde.chemin(), monde.saisie(fatigue="1") | {"date": LENDEMAIN.isoformat()})

    assert 'value="23:30"' not in page
    assert _enregistre(monde, jour=JOUR)["fatigue"] == 4
    assert _enregistre(monde, jour=LENDEMAIN)["fatigue"] == 1
    assert EntreeSensations.objects.filter(joueur=monde.dupont).count() == 2


# --- CSRF ------------------------------------------------------------------------------


def test_le_formulaire_est_protege_contre_la_falsification_de_requete(monde: Monde) -> None:
    client = Client(enforce_csrf_checks=True)

    refus = client.post(monde.chemin(), monde.saisie())
    page = client.get(monde.chemin()).content.decode()
    jeton_csrf = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', page)
    assert jeton_csrf
    accepte = client.post(monde.chemin(), monde.saisie() | {"csrfmiddlewaretoken": jeton_csrf[1]})

    assert refus.status_code == 403
    assert accepte.status_code == 200
    assert _enregistre(monde)["fatigue"] == 4


def test_le_jeton_n_est_pas_journalise_quand_le_controle_csrf_refuse_l_envoi(
    monde: Monde, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.DEBUG):
        reponse = Client(enforce_csrf_checks=True).post(monde.chemin(), monde.saisie())

    assert reponse.status_code == 403
    assert "django.security.csrf" in {r.name for r in caplog.records}
    assert monde.jeton not in caplog.text
    assert all(monde.jeton not in str(enregistrement.args) for enregistrement in caplog.records)


def test_un_envoi_ne_cree_pas_d_entree_quand_aucun_indicateur_n_est_actif(monde: Monde) -> None:
    Indicateur.objects.filter(categorie=monde.u19).update(actif=False)

    reponse = Client().post(monde.chemin(), {"date": JOUR.isoformat()})

    assert reponse.status_code == 200
    assert EntreeSensations.objects.count() == 0
    assert "Aucune question" in reponse.content.decode()


def test_une_erreur_apres_minuit_ne_fait_pas_perdre_les_reponses_deux_fois(
    monde: Monde, monkeypatch: pytest.MonkeyPatch
) -> None:
    client = Client()
    monkeypatch.setattr("suivi.views.questionnaire.aujourd_hui", lambda: LENDEMAIN)

    page = client.post(monde.chemin(), monde.saisie(fatigue="11")).content.decode()
    assert f'value="{LENDEMAIN.isoformat()}"' in page

    corrige = client.post(monde.chemin(), monde.saisie() | {"date": LENDEMAIN.isoformat()})

    assert "nouvelle journée" not in corrige.content.decode()
    assert _enregistre(monde, jour=LENDEMAIN)["fatigue"] == 4


def test_un_lien_revoque_pendant_l_envoi_n_ecrit_rien(monde: Monde) -> None:
    from suivi.liens import empreinte
    from suivi.questionnaire import LienPerime, enregistrer_entree

    ancienne_empreinte = empreinte(monde.jeton)
    creer_lien(monde.dupont, monde.compte)  # régénéré entre la lecture du lien et l'écriture

    with pytest.raises(LienPerime):
        enregistrer_entree(monde.dupont, JOUR, {monde.fatigue.pk: 4}, ancienne_empreinte)

    assert EntreeSensations.objects.count() == 0


def test_un_joueur_archive_pendant_l_envoi_n_ecrit_rien(monde: Monde) -> None:
    from suivi.liens import empreinte
    from suivi.questionnaire import LienPerime, enregistrer_entree

    LienJoueur.objects.filter(joueur=monde.dupont).update(revoked_at=None)
    Joueur.objects.filter(pk=monde.dupont.pk).update(actif=False)

    with pytest.raises(LienPerime):
        enregistrer_entree(monde.dupont, JOUR, {monde.fatigue.pk: 4}, empreinte(monde.jeton))

    assert EntreeSensations.objects.count() == 0


def test_la_modification_par_le_joueur_remet_l_auteur_a_nul(monde: Monde) -> None:
    EntreeSensations.objects.create(joueur=monde.dupont, date=JOUR, updated_by=monde.compte)

    Client().post(monde.chemin(), monde.saisie())

    assert EntreeSensations.objects.get().updated_by is None


def test_un_preparateur_connecte_ne_voit_ni_navigation_ni_messages_sur_la_page_du_joueur(
    monde: Monde,
) -> None:
    client = Client()
    client.force_login(monde.compte)
    client.post(f"/joueurs/{monde.petit.pk}/lien/revoquer/")  # pose un message en attente

    page = client.get(monde.chemin()).content.decode()

    assert "n’a pas de lien actif" not in page
    assert "Se déconnecter" not in page
    assert "/joueurs/" not in page
    assert "Fatigue" in page


def test_les_refus_de_methode_ne_sont_pas_mis_en_cache(monde: Monde) -> None:
    reponse = Client().put(monde.chemin())

    assert reponse.status_code == 405
    assert "no-store" in reponse["Cache-Control"]
