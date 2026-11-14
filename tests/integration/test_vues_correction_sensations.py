"""Correction et suppression d'une entrée de sensations passée par le préparateur
(F17, ADR-0008 Q3, A3, D1)."""

import datetime
import logging
import re

import pytest
from django.contrib.auth.models import User
from django.test import Client

from engine.modeles import Parametres
from suivi.calculs import calculer_sensations
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

pytestmark = pytest.mark.django_db

NAISSANCE = datetime.date(2007, 3, 14)
HIER = datetime.date(2026, 11, 12)
AVANT_HIER = datetime.date(2026, 11, 11)
PARAMETRES = Parametres(10, 7, 28, 28, 21, 1e-9, 0.5, 28, 6, 3, 3)


class Monde:
    def __init__(self) -> None:
        self.u19 = Categorie.objects.create(code="U19", libelle="U19")
        self.u17 = Categorie.objects.create(code="U17", libelle="U17")
        self.compte19 = User.objects.create_user("p19")
        self.compte17 = User.objects.create_user("p17")
        Preparateur.objects.create(user=self.compte19, categorie=self.u19)
        Preparateur.objects.create(user=self.compte17, categorie=self.u17)
        self.fatigue = self.note(self.u19, "fatigue", "Fatigue", 1)
        self.plaisir = self.note(self.u19, "plaisir", "Plaisir", 2)
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
        self.ancien = self.note(self.u19, "ancien", "Indicateur retiré", 4, actif=False)
        self.note(self.u17, "fatigue", "Fatigue U17", 1)
        self.note(self.u17, "plaisir", "Plaisir U17", 2)
        self.dupont = self.joueur("Dupont", self.u19)
        self.petit = self.joueur("Petit", self.u19)
        self.sans_entree = self.joueur("Vide", self.u19)
        self.leroy = self.joueur("Leroy", self.u17)
        self.invite = self.joueur("Invite", self.u17)
        seance = Seance.objects.create(
            categorie_organisatrice=self.u19, date=HIER, type="foot", duree_min=60
        )
        Participation.objects.create(seance=seance, joueur=self.invite)
        self.hier = self.entree(self.dupont, HIER, fatigue=4, plaisir=8, heure_coucher=1410)
        self.avant_hier = self.entree(self.dupont, AVANT_HIER, fatigue=2, plaisir=6)
        self.entree_petit = self.entree(self.petit, HIER, fatigue=1, plaisir=1)
        self.entree_invite = self.entree(self.invite, HIER, fatigue=9, plaisir=9)

    @staticmethod
    def note(
        categorie: Categorie, code: str, libelle: str, ordre: int, actif: bool = True
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
    def joueur(nom: str, categorie: Categorie) -> Joueur:
        return Joueur.objects.create(
            nom=nom, prenom="Test", date_naissance=NAISSANCE, categorie_reference=categorie
        )

    def entree(self, joueur: Joueur, jour: datetime.date, **valeurs: int) -> EntreeSensations:
        entree = EntreeSensations.objects.create(joueur=joueur, date=jour)
        for code, valeur in valeurs.items():
            indicateur = Indicateur.objects.get(code=code, categorie=joueur.categorie_reference)
            Reponse.objects.create(entree=entree, indicateur=indicateur, valeur=valeur)
        return entree

    def client(self, compte: User | None = None) -> Client:
        client = Client()
        client.force_login(compte or self.compte19)
        return client

    def chemin(
        self, joueur: Joueur, entree: EntreeSensations | None = None, action: str = ""
    ) -> str:
        base = f"/joueurs/{joueur.pk}/sensations/"
        return base if entree is None else f"{base}{entree.pk}/{action}"

    def saisie(self, **valeurs: str) -> dict[str, str]:
        champs = {
            f"i{self.fatigue.pk}": "",
            f"i{self.plaisir.pk}": "",
            f"i{self.coucher.pk}": "",
        }
        for code, valeur in valeurs.items():
            indicateur = Indicateur.objects.get(code=code, categorie=self.u19)
            champs[f"i{indicateur.pk}"] = valeur
        return champs


AUJOURDHUI = datetime.date(2026, 11, 13)


@pytest.fixture
def monde(monkeypatch: pytest.MonkeyPatch) -> Monde:
    monkeypatch.setattr("suivi.views.staff.aujourd_hui", lambda: AUJOURDHUI)
    return Monde()


def _valeurs(entree: EntreeSensations) -> dict[str, int]:
    return {r.indicateur.code: r.valeur for r in entree.reponses.select_related("indicateur")}


# --- Liste -----------------------------------------------------------------------------


def test_la_liste_montre_les_entrees_du_joueur_des_plus_recentes_aux_plus_anciennes(
    monde: Monde,
) -> None:
    reponse = monde.client().get(monde.chemin(monde.dupont))

    page = reponse.content.decode()
    assert reponse.status_code == 200
    assert "Dupont" in page
    assert page.index("12/11/2026") < page.index("11/11/2026")
    assert monde.chemin(monde.dupont, monde.hier, "corriger/") in page
    assert monde.chemin(monde.dupont, monde.hier, "supprimer/") in page
    assert monde.chemin(monde.dupont, monde.entree_petit) not in page


def test_la_liste_affiche_la_trace_d_une_correction(monde: Monde) -> None:
    EntreeSensations.objects.filter(pk=monde.hier.pk).update(updated_by=monde.compte19)

    page = monde.client().get(monde.chemin(monde.dupont)).content.decode()

    assert "corrigée par p19" in page


def test_la_liste_d_un_joueur_sans_entree_le_dit(monde: Monde) -> None:
    assert "Aucune entrée" in monde.client().get(monde.chemin(monde.sans_entree)).content.decode()


def test_la_page_des_joueurs_renvoie_vers_les_sensations(monde: Monde) -> None:
    page = monde.client().get("/joueurs/").content.decode()

    assert monde.chemin(monde.dupont) in page


def test_un_joueur_archive_garde_ses_entrees_corrigeables(monde: Monde) -> None:
    Joueur.objects.filter(pk=monde.dupont.pk).update(actif=False)

    assert monde.client().get(monde.chemin(monde.dupont)).status_code == 200
    assert (
        monde.client().get(monde.chemin(monde.dupont, monde.hier, "corriger/")).status_code == 200
    )


# --- A3 : périmètre --------------------------------------------------------------------

ACTIONS = ["", "corriger/", "supprimer/"]


@pytest.mark.parametrize("action", ACTIONS)
@pytest.mark.parametrize("methode", ["get", "post"])
def test_a3_un_autre_preparateur_ne_touche_pas_aux_entrees_de_mes_joueurs(
    monde: Monde, action: str, methode: str
) -> None:
    client = monde.client(monde.compte17)
    chemin = monde.chemin(monde.dupont, monde.hier if action else None, action)

    reponse = getattr(client, methode)(chemin, monde.saisie(fatigue="0"))

    # La liste est en lecture seule : un POST y est refusé avant tout accès aux données.
    assert reponse.status_code == (405 if (action, methode) == ("", "post") else 404)
    assert EntreeSensations.objects.filter(pk=monde.hier.pk).exists()
    assert _valeurs(monde.hier)["fatigue"] == 4


@pytest.mark.parametrize("action", ACTIONS)
@pytest.mark.parametrize("methode", ["get", "post"])
def test_a3_le_preparateur_organisateur_ne_touche_pas_a_l_entree_d_un_joueur_invite(
    monde: Monde, action: str, methode: str
) -> None:
    chemin = monde.chemin(monde.invite, monde.entree_invite if action else None, action)

    reponse = getattr(monde.client(), methode)(chemin, monde.saisie(fatigue="0"))

    assert reponse.status_code == (405 if (action, methode) == ("", "post") else 404)
    assert EntreeSensations.objects.filter(pk=monde.entree_invite.pk).exists()
    assert _valeurs(monde.entree_invite)["fatigue"] == 9


@pytest.mark.parametrize("action", ["corriger/", "supprimer/"])
def test_a3_l_entree_d_un_autre_joueur_ne_passe_pas_par_l_adresse_d_un_joueur_suivi(
    monde: Monde, action: str
) -> None:
    chemin = monde.chemin(monde.dupont, monde.entree_petit, action)

    assert monde.client().get(chemin).status_code == 404
    assert monde.client().post(chemin, monde.saisie(fatigue="0")).status_code == 404
    assert _valeurs(monde.entree_petit)["fatigue"] == 1


def test_a3_une_entree_inexistante_donne_404(monde: Monde) -> None:
    assert (
        monde.client().get(f"/joueurs/{monde.dupont.pk}/sensations/99999/corriger/").status_code
        == 404
    )


# --- Correction ------------------------------------------------------------------------


def test_le_formulaire_est_prerempli_avec_l_entree_et_sans_indicateur_desactive(
    monde: Monde,
) -> None:
    page = monde.client().get(monde.chemin(monde.dupont, monde.hier, "corriger/")).content.decode()

    assert 'value="4"' in page and 'value="8"' in page and 'value="23:30"' in page
    assert "Indicateur retiré" not in page
    assert "12/11/2026" in page
    assert 'name="date"' not in page  # la date d'une entrée ne se change pas


def test_une_correction_modifie_les_valeurs_la_date_et_l_auteur(monde: Monde) -> None:
    avant = EntreeSensations.objects.get(pk=monde.hier.pk).updated_at

    reponse = monde.client().post(
        monde.chemin(monde.dupont, monde.hier, "corriger/"),
        monde.saisie(fatigue="7", plaisir="8", heure_coucher="00:15"),
    )

    assert reponse.status_code == 302
    assert reponse["Location"] == monde.chemin(monde.dupont)
    entree = EntreeSensations.objects.get(pk=monde.hier.pk)
    assert _valeurs(entree) == {"fatigue": 7, "plaisir": 8, "heure_coucher": 15}
    assert entree.date == HIER
    assert entree.updated_by == monde.compte19
    assert entree.updated_at > avant
    assert EntreeSensations.objects.filter(joueur=monde.dupont).count() == 2


def test_une_correction_laisse_les_autres_entrees_intactes(monde: Monde) -> None:
    monde.client().post(
        monde.chemin(monde.dupont, monde.hier, "corriger/"), monde.saisie(fatigue="7")
    )

    assert _valeurs(monde.avant_hier) == {"fatigue": 2, "plaisir": 6}
    assert _valeurs(monde.entree_petit) == {"fatigue": 1, "plaisir": 1}
    assert EntreeSensations.objects.get(pk=monde.avant_hier.pk).updated_by is None


def test_un_champ_laisse_vide_ne_change_pas_la_reponse(monde: Monde) -> None:
    monde.client().post(
        monde.chemin(monde.dupont, monde.hier, "corriger/"), monde.saisie(fatigue="7")
    )

    assert _valeurs(monde.hier) == {"fatigue": 7, "plaisir": 8, "heure_coucher": 1410}


def test_un_indicateur_sans_reponse_peut_etre_ajoute_a_une_ancienne_entree(monde: Monde) -> None:
    monde.client().post(
        monde.chemin(monde.dupont, monde.avant_hier, "corriger/"),
        monde.saisie(heure_coucher="22:00"),
    )

    assert _valeurs(monde.avant_hier) == {"fatigue": 2, "plaisir": 6, "heure_coucher": 1320}


def test_une_correction_sans_valeur_ne_change_rien_et_le_dit(monde: Monde) -> None:
    avant = EntreeSensations.objects.get(pk=monde.hier.pk).updated_at
    client = monde.client()

    reponse = client.post(monde.chemin(monde.dupont, monde.hier, "corriger/"), monde.saisie())

    entree = EntreeSensations.objects.get(pk=monde.hier.pk)
    assert reponse.status_code == 302
    assert entree.updated_at == avant and entree.updated_by is None
    assert "Aucune modification" in client.get(monde.chemin(monde.dupont)).content.decode()


def test_la_correction_conserve_la_reponse_d_un_indicateur_desactive(monde: Monde) -> None:
    Reponse.objects.create(entree=monde.hier, indicateur=monde.ancien, valeur=6)

    monde.client().post(
        monde.chemin(monde.dupont, monde.hier, "corriger/"), monde.saisie(fatigue="7")
    )

    assert _valeurs(monde.hier)["ancien"] == 6  # ADR-0016


@pytest.mark.parametrize(
    "valeurs",
    [
        {"fatigue": "11"},
        {"fatigue": "-1"},
        {"fatigue": "4.5"},
        {"fatigue": "x"},
        {"heure_coucher": "24:00"},
    ],
    ids=lambda v: "=".join(next(iter(v.items()))),
)
def test_d1_une_valeur_hors_echelle_est_refusee_sans_rien_changer(
    monde: Monde, valeurs: dict[str, str]
) -> None:
    reponse = monde.client().post(
        monde.chemin(monde.dupont, monde.hier, "corriger/"), monde.saisie(plaisir="1", **valeurs)
    )

    assert reponse.status_code == 200
    assert 'class="erreur"' in reponse.content.decode()
    assert _valeurs(monde.hier) == {"fatigue": 4, "plaisir": 8, "heure_coucher": 1410}
    assert EntreeSensations.objects.get(pk=monde.hier.pk).updated_by is None


def test_une_correction_ne_peut_viser_ni_une_autre_date_ni_un_autre_joueur(monde: Monde) -> None:
    champs = monde.saisie(fatigue="7") | {
        "date": AVANT_HIER.isoformat(),
        "joueur": str(monde.petit.pk),
        "updated_by": "1",
    }

    monde.client().post(monde.chemin(monde.dupont, monde.hier, "corriger/"), champs)

    entree = EntreeSensations.objects.get(pk=monde.hier.pk)
    assert (entree.joueur, entree.date) == (monde.dupont, HIER)
    assert entree.updated_by == monde.compte19  # jamais celui du formulaire
    assert _valeurs(monde.entree_petit)["fatigue"] == 1


def test_la_correction_se_repercute_dans_le_score_de_sensations(monde: Monde) -> None:
    avant, _ = calculer_sensations(monde.dupont.pk, HIER, PARAMETRES)
    # fatigue 4 et plaisir 8, tous deux « bas = bon » sur 0 à 10 : (0,6 + 0,2) / 2.
    assert avant[-1].valeur == pytest.approx(0.4)

    monde.client().post(
        monde.chemin(monde.dupont, monde.hier, "corriger/"), monde.saisie(fatigue="0")
    )

    apres, _ = calculer_sensations(monde.dupont.pk, HIER, PARAMETRES)
    assert apres[-1].valeur == pytest.approx(0.6)  # (1,0 + 0,2) / 2


def test_la_correction_exige_la_protection_csrf(monde: Monde) -> None:
    client = Client(enforce_csrf_checks=True)
    client.force_login(monde.compte19)

    reponse = client.post(
        monde.chemin(monde.dupont, monde.hier, "corriger/"), monde.saisie(fatigue="7")
    )

    assert reponse.status_code == 403
    assert _valeurs(monde.hier)["fatigue"] == 4


# --- Suppression -----------------------------------------------------------------------


def test_la_page_de_suppression_demande_confirmation_sans_rien_supprimer(monde: Monde) -> None:
    reponse = monde.client().get(monde.chemin(monde.dupont, monde.hier, "supprimer/"))

    page = reponse.content.decode()
    assert reponse.status_code == 200
    assert "définitive" in page and "Dupont" in page and "12/11/2026" in page
    assert EntreeSensations.objects.filter(pk=monde.hier.pk).exists()


def test_la_suppression_retire_l_entree_et_ses_reponses_seulement(monde: Monde) -> None:
    reponse = monde.client().post(monde.chemin(monde.dupont, monde.hier, "supprimer/"))

    assert reponse.status_code == 302
    assert reponse["Location"] == monde.chemin(monde.dupont)
    assert not EntreeSensations.objects.filter(pk=monde.hier.pk).exists()
    assert not Reponse.objects.filter(entree_id=monde.hier.pk).exists()
    assert _valeurs(monde.avant_hier) == {"fatigue": 2, "plaisir": 6}
    assert EntreeSensations.objects.filter(pk=monde.entree_petit.pk).exists()
    assert EntreeSensations.objects.filter(pk=monde.entree_invite.pk).exists()


def test_apres_une_suppression_le_joueur_peut_redeposer_cette_date(monde: Monde) -> None:
    monde.client().post(monde.chemin(monde.dupont, monde.hier, "supprimer/"))

    EntreeSensations.objects.create(joueur=monde.dupont, date=HIER)  # pas de doublon fantôme

    assert EntreeSensations.objects.filter(joueur=monde.dupont, date=HIER).count() == 1


def test_la_suppression_est_tracee_au_journal_par_cles_sans_nom(
    monde: Monde, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.INFO, logger="suivi.audit"):
        monde.client().post(monde.chemin(monde.dupont, monde.hier, "supprimer/"))

    messages = [r.getMessage() for r in caplog.records if r.name == "suivi.audit"]
    assert len(messages) == 1
    assert f"joueur={monde.dupont.pk} " in messages[0]
    assert "date=2026-11-12" in messages[0]
    assert messages[0].endswith(f" par={monde.compte19.pk}")
    assert "p19" not in messages[0]
    assert "Dupont" not in messages[0]


def test_la_suppression_n_a_lieu_qu_en_post_et_avec_csrf(monde: Monde) -> None:
    client = Client(enforce_csrf_checks=True)
    client.force_login(monde.compte19)

    reponse = client.post(monde.chemin(monde.dupont, monde.hier, "supprimer/"))

    assert reponse.status_code == 403
    assert EntreeSensations.objects.filter(pk=monde.hier.pk).exists()
    assert (
        monde.client().put(monde.chemin(monde.dupont, monde.hier, "supprimer/")).status_code == 405
    )


def test_un_visiteur_anonyme_est_renvoye_vers_la_connexion(monde: Monde) -> None:
    for action in ACTIONS:
        chemin = monde.chemin(monde.dupont, monde.hier if action else None, action)
        reponse = Client().get(chemin)
        assert reponse.status_code == 302
        assert "/connexion/" in reponse["Location"]
        assert re.search(r"Dupont", reponse.content.decode()) is None


def test_un_envoi_sans_reponse_modifiee_n_est_pas_une_correction(monde: Monde) -> None:
    avant = EntreeSensations.objects.get(pk=monde.hier.pk).updated_at
    chemin = monde.chemin(monde.dupont, monde.hier, "corriger/")
    client = monde.client()
    page = client.get(chemin).content.decode()
    champs = dict(re.findall(r'name="(i\d+)"[^>]*value="([^"]*)"', page))
    assert len(champs) == 3  # le navigateur renvoie le formulaire prérempli tel quel

    client.post(chemin, champs)

    entree = EntreeSensations.objects.get(pk=monde.hier.pk)
    assert entree.updated_at == avant and entree.updated_by is None
    assert "inchangées" in client.get(monde.chemin(monde.dupont)).content.decode()


def test_seule_la_reponse_modifiee_est_ecrite_et_tracee(monde: Monde) -> None:
    monde.client().post(
        monde.chemin(monde.dupont, monde.hier, "corriger/"),
        monde.saisie(fatigue="4", plaisir="1", heure_coucher="23:30"),
    )

    assert _valeurs(monde.hier) == {"fatigue": 4, "plaisir": 1, "heure_coucher": 1410}
    assert EntreeSensations.objects.get(pk=monde.hier.pk).updated_by == monde.compte19


@pytest.fixture
def entree_du_jour(monde: Monde) -> EntreeSensations:
    return monde.entree(monde.dupont, AUJOURDHUI, fatigue=5, plaisir=5)


@pytest.mark.parametrize("action", ["corriger/", "supprimer/"])
@pytest.mark.parametrize("methode", ["get", "post"])
def test_r16_l_entree_du_jour_n_est_pas_corrigeable_par_le_preparateur(
    monde: Monde, entree_du_jour: EntreeSensations, action: str, methode: str
) -> None:
    chemin = monde.chemin(monde.dupont, entree_du_jour, action)

    reponse = getattr(monde.client(), methode)(chemin, monde.saisie(fatigue="0"))

    assert reponse.status_code == 404
    assert _valeurs(entree_du_jour) == {"fatigue": 5, "plaisir": 5}


def test_la_liste_ne_propose_ni_correction_ni_suppression_pour_le_jour_en_cours(
    monde: Monde, entree_du_jour: EntreeSensations
) -> None:
    page = monde.client().get(monde.chemin(monde.dupont)).content.decode()

    assert monde.chemin(monde.dupont, entree_du_jour, "corriger/") not in page
    assert monde.chemin(monde.dupont, entree_du_jour, "supprimer/") not in page
    assert "le joueur la modifie par son lien" in page
    assert monde.chemin(monde.dupont, monde.hier, "corriger/") in page


# --- Concurrence et journal ------------------------------------------------------------


def test_une_correction_apres_une_suppression_ne_recree_pas_l_entree(monde: Monde) -> None:
    from suivi.questionnaire import EntreeSupprimee, corriger_entree, supprimer_entree

    lue = EntreeSensations.objects.get(pk=monde.hier.pk)  # lue avant la suppression
    supprimer_entree(lue, monde.compte19)

    with pytest.raises(EntreeSupprimee):
        corriger_entree(lue, {monde.fatigue.pk: 7}, monde.compte19)

    assert not EntreeSensations.objects.filter(pk=monde.hier.pk).exists()
    assert not Reponse.objects.filter(entree_id=monde.hier.pk).exists()


def test_une_seconde_suppression_ne_laisse_pas_de_seconde_trace(
    monde: Monde, caplog: pytest.LogCaptureFixture
) -> None:
    from suivi.questionnaire import EntreeSupprimee, supprimer_entree

    lue = EntreeSensations.objects.get(pk=monde.hier.pk)
    with caplog.at_level(logging.INFO, logger="suivi.audit"):
        supprimer_entree(lue, monde.compte19)
        with pytest.raises(EntreeSupprimee):
            supprimer_entree(lue, monde.compte19)

    assert len([r for r in caplog.records if r.name == "suivi.audit"]) == 1


def test_une_correction_d_une_entree_disparue_donne_404(monde: Monde) -> None:
    chemin = monde.chemin(monde.dupont, monde.hier, "corriger/")
    EntreeSensations.objects.filter(pk=monde.hier.pk).delete()

    assert monde.client().post(chemin, monde.saisie(fatigue="7")).status_code == 404


def test_le_journal_d_audit_est_actif_sans_reglage_de_test() -> None:
    journal = logging.getLogger("suivi.audit")

    assert journal.isEnabledFor(logging.INFO)
    assert journal.handlers


def test_une_correction_ne_cree_pas_de_reponse_pour_un_autre_indicateur(monde: Monde) -> None:
    autre = Indicateur.objects.get(code="fatigue", categorie=monde.u17)
    champs = monde.saisie(fatigue="7") | {f"i{autre.pk}": "0", f"i{monde.ancien.pk}": "0"}

    monde.client().post(monde.chemin(monde.dupont, monde.hier, "corriger/"), champs)

    assert _valeurs(monde.hier) == {"fatigue": 7, "plaisir": 8, "heure_coucher": 1410}
    assert not Reponse.objects.filter(
        entree=monde.hier, indicateur__in=[autre, monde.ancien]
    ).exists()
