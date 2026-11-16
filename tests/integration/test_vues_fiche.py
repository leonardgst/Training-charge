"""Fiche joueur, charge (US-11, F12) : périmètre d'accès (A3) et valeurs du moteur."""

import datetime
import json
import re
import secrets
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client
from django.utils import timezone

from suivi.calculs import calculer_charges_glissantes, calculer_detail_sensations, parametres
from suivi.models import (
    Categorie,
    EntreeSensations,
    Indicateur,
    Joueur,
    Participation,
    Preparateur,
    Reponse,
    Seance,
    StatutSeance,
)

pytestmark = pytest.mark.django_db

FIN = datetime.date(2026, 10, 30)


@pytest.fixture
def demo(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("suivi.views.fiche.aujourd_hui", lambda: FIN)
    call_command("generer_demo", fin=FIN, mot_de_passe=secrets.token_urlsafe(12), verbosity=0)


def _client(compte: str) -> Client:
    client = Client()
    client.force_login(get_user_model().objects.get(username=compte))
    return client


def _joueur(categorie: str) -> Joueur:
    return Joueur.objects.filter(categorie_reference__code=categorie, actif=True).first()  # type: ignore[return-value]


def test_un_visiteur_anonyme_est_renvoye_vers_la_connexion() -> None:
    reponse = Client().get("/joueurs/1/")
    assert reponse.status_code == 302
    assert "/connexion/" in reponse["Location"]


def test_a3_la_fiche_d_un_joueur_d_une_autre_categorie_ou_inexistant_repond_404(
    demo: None,
) -> None:
    client = _client("prep_u19")
    assert client.get(f"/joueurs/{_joueur('U17').pk}/").status_code == 404
    assert client.get("/joueurs/999999/").status_code == 404


def test_a3_la_fiche_d_un_invite_repond_404_et_ne_fuit_pas_son_nom(demo: None) -> None:
    invite = (
        Joueur.objects.filter(
            categorie_reference__code="U17",
            participations__seance__categorie_organisatrice__code="U19",
        )
        .distinct()
        .first()
    )
    assert invite is not None
    reponse = _client("prep_u19").get(f"/joueurs/{invite.pk}/")
    assert reponse.status_code == 404
    assert invite.nom not in reponse.content.decode()


def test_la_fiche_affiche_les_rpe_et_les_charges_du_moteur(demo: None) -> None:
    joueur = _joueur("U19")
    page = _client("prep_u19").get(f"/joueurs/{joueur.pk}/").content.decode()
    tableau = page.split('id="rpe-seances"')[1].split("</table>")[0]
    assert tableau.count('class="rpe"') % 3 == 0 and 'class="rpe"' in tableau
    derniere = (
        Participation.objects.filter(joueur=joueur, seance__statut=StatutSeance.VALIDEE)
        .order_by("-seance__date")
        .first()
    )
    assert derniere is not None
    assert f'data-niveau="{derniere.rpe_cardio}"' in tableau
    bloc = re.search(r'<script id="specification-forme"[^>]*>(.*?)</script>', page, re.S)
    assert bloc
    valeurs = json.loads(bloc.group(1))["data"]["values"]
    attendu = calculer_charges_glissantes(joueur.pk, FIN, parametres())[-1]
    du_jour = {v["grandeur"]: v["valeur"] for v in valeurs if v["jour"] == FIN.isoformat()}
    assert du_jour["CE courte"] == pytest.approx(attendu.ce_courte)
    assert du_jour["CE longue"] == pytest.approx(attendu.ce_longue)
    assert 'id="valeurs-charge"' in page


def test_un_brouillon_n_entre_pas_dans_la_fiche(demo: None) -> None:
    joueur = _joueur("U19")
    avant = _client("prep_u19").get(f"/joueurs/{joueur.pk}/").content.decode()
    brouillon = Seance.objects.create(
        categorie_organisatrice=joueur.categorie_reference,
        date=FIN,
        type="foot",
        duree_min=240,
    )
    Participation.objects.create(
        seance=brouillon, joueur=joueur, rpe_cardio=10, rpe_musculaire=10, rpe_teta=10
    )
    apres = _client("prep_u19").get(f"/joueurs/{joueur.pk}/").content.decode()
    jeton = r'name="csrfmiddlewaretoken" value="[^"]+"'
    assert re.sub(jeton, "", avant) == re.sub(jeton, "", apres)


def test_un_joueur_sans_seance_a_une_fiche_vide_sans_erreur() -> None:
    u19 = Categorie.objects.create(code="U19", libelle="U19")
    compte = get_user_model().objects.create_user("p19")
    Preparateur.objects.create(user=compte, categorie=u19)
    neuf = Joueur.objects.create(
        nom="Neuf",
        prenom="Test",
        date_naissance=datetime.date(2007, 3, 14),
        categorie_reference=u19,
    )
    client = Client()
    client.force_login(compte)
    with patch("suivi.views.fiche.aujourd_hui", return_value=FIN):
        reponse = client.get(f"/joueurs/{neuf.pk}/")
    assert reponse.status_code == 200
    assert "Aucune séance validée" in reponse.content.decode()


def test_la_fiche_n_accepte_aucune_ecriture(demo: None) -> None:
    assert _client("prep_u19").post(f"/joueurs/{_joueur('U19').pk}/").status_code == 405


def test_la_fiche_ne_depend_d_aucun_script_ni_style_en_ligne(demo: None) -> None:
    page = _client("prep_u19").get(f"/joueurs/{_joueur('U19').pk}/").content.decode()
    assert "<style" not in page
    assert not re.search(r"\sstyle\s*=", page)


def _invite_u17() -> Joueur:
    invite = (
        Joueur.objects.filter(
            categorie_reference__code="U17",
            participations__seance__categorie_organisatrice__code="U19",
            participations__seance__statut=StatutSeance.VALIDEE,
        )
        .distinct()
        .first()
    )
    assert invite is not None
    return invite


def test_a3_dans_l_autre_sens_un_u17_ne_voit_pas_la_fiche_d_un_u19(demo: None) -> None:
    assert _client("prep_u17").get(f"/joueurs/{_joueur('U19').pk}/").status_code == 404


def test_a3_un_u17_non_invite_repond_404_pour_le_preparateur_u19(demo: None) -> None:
    non_invite = (
        Joueur.objects.filter(categorie_reference__code="U17", actif=True)
        .exclude(participations__seance__categorie_organisatrice__code="U19")
        .first()
    )
    assert non_invite is not None
    client = _client("prep_u19")
    assert client.get(f"/joueurs/{non_invite.pk}/").status_code == 404
    assert client.head(f"/joueurs/{non_invite.pk}/").status_code == 404


def test_la_fiche_d_un_invite_montre_ses_seances_chez_les_u19_sans_lien_casse(
    demo: None,
) -> None:
    client = _client("prep_u17")
    page = client.get(f"/joueurs/{_invite_u17().pk}/").content.decode()
    tableau = page.split('id="rpe-seances"')[1].split("</table>")[0]
    assert tableau.count("<tr>") > 1
    liens = re.findall(r'href="(/seances/\d+/)"', tableau)
    for lien in liens:
        assert client.get(lien).status_code == 200


def test_les_etats_et_les_fenetres_incompletes_sont_affiches() -> None:
    u19 = Categorie.objects.create(code="U19", libelle="U19")
    compte = get_user_model().objects.create_user("p19")
    Preparateur.objects.create(user=compte, categorie=u19)
    joueur = Joueur.objects.create(
        nom="Recrue",
        prenom="Test",
        date_naissance=datetime.date(2007, 3, 14),
        categorie_reference=u19,
    )
    for decalage in (3, 1):
        seance = Seance.objects.create(
            categorie_organisatrice=u19,
            date=FIN - datetime.timedelta(days=decalage),
            type="foot",
            duree_min=60,
        )
        Participation.objects.create(
            seance=seance, joueur=joueur, rpe_cardio=5, rpe_musculaire=5, rpe_teta=5
        )
        Seance.objects.filter(pk=seance.pk).update(
            statut=StatutSeance.VALIDEE, validated_at=timezone.now()
        )
    # Séance validée datée après le jour de calcul : absente de la fiche.
    futur = Seance.objects.create(
        categorie_organisatrice=u19,
        date=FIN + datetime.timedelta(days=1),
        type="foot",
        duree_min=61,
    )
    Participation.objects.create(
        seance=futur, joueur=joueur, rpe_cardio=9, rpe_musculaire=9, rpe_teta=9
    )
    Seance.objects.filter(pk=futur.pk).update(
        statut=StatutSeance.VALIDEE, validated_at=timezone.now()
    )
    client = Client()
    client.force_login(compte)
    with patch("suivi.views.fiche.aujourd_hui", return_value=FIN):
        page = client.get(f"/joueurs/{joueur.pk}/").content.decode()
    assert "Historique insuffisant" in page
    assert "Fenêtre incomplète" in page
    assert "<td>—</td>" in page
    tableau = page.split('id="rpe-seances"')[1].split("</table>")[0]
    assert tableau.count('class="rpe"') == 6
    assert 'data-niveau="9"' not in tableau


# --- Sensations (PR 6.3) ----------------------------------------------------------------


def _specification(page: str, identifiant: str) -> dict:
    bloc = re.search(rf'<script id="{identifiant}"[^>]*>(.*?)</script>', page, re.S)
    assert bloc, identifiant
    return json.loads(bloc.group(1))


def test_la_fiche_affiche_les_sensations_du_moteur(demo: None) -> None:
    joueur = _joueur("U19")
    page = _client("prep_u19").get(f"/joueurs/{joueur.pk}/").content.decode()
    attendu = calculer_detail_sensations(joueur.pk, FIN, parametres())
    assert attendu.derniere is not None and attendu.derniere.total is not None

    barres = _specification(page, "specification-barres")["data"]["values"]
    niveaux = {c.code: c.niveau for c in attendu.derniere.cellules if c.niveau is not None}
    assert {b["indicateur"]: b["niveau"] for b in barres} == pytest.approx(
        {attendu.libelles[code]: n for code, n in niveaux.items()}
    )

    cellules = _specification(page, "specification-heatmap")["data"]["values"]
    totaux = {c["jour"]: c["niveau"] for c in cellules if c["indicateur"] == "Total"}
    for jour in attendu.jours:
        if jour.total is not None:
            assert totaux[jour.jour.strftime("%d/%m")] == pytest.approx(jour.total)
    assert 'id="valeurs-derniere-entree"' in page and 'id="valeurs-heatmap"' in page
    tableau = page.split('id="valeurs-heatmap"')[1].split("</table>")[0]
    assert tableau.count('<th scope="col">') == 1 + 7
    assert "Total" in tableau


def test_les_indicateurs_hors_score_ne_sont_pas_affiches(demo: None) -> None:
    # Le U19 de la démonstration a des indicateurs d'heure : sans niveau sur 10, ils restent
    # hors des barres et de la heatmap.
    joueur = _joueur("U19")
    page = _client("prep_u19").get(f"/joueurs/{joueur.pk}/").content.decode()
    heures = Indicateur.objects.filter(categorie=joueur.categorie_reference, type="heure")
    assert heures.exists()
    for indicateur in heures:
        assert indicateur.libelle not in page


def test_c9_les_sensations_de_la_fiche_ignorent_les_entrees_posterieures(demo: None) -> None:
    joueur = _joueur("U19")
    avant = _client("prep_u19").get(f"/joueurs/{joueur.pk}/").content.decode()
    futur = EntreeSensations.objects.create(joueur=joueur, date=FIN + datetime.timedelta(days=1))
    for indicateur in Indicateur.objects.filter(
        categorie=joueur.categorie_reference, type="note", inclus_score=True
    ):
        Reponse.objects.create(entree=futur, indicateur=indicateur, valeur=indicateur.borne_min)
    apres = _client("prep_u19").get(f"/joueurs/{joueur.pk}/").content.decode()
    jeton = r'name="csrfmiddlewaretoken" value="[^"]+"'
    assert re.sub(jeton, "", avant) == re.sub(jeton, "", apres)


def test_a3_les_entrees_d_un_invite_d_une_autre_categorie_ne_changent_pas_la_fiche(
    demo: None,
) -> None:
    joueur = _joueur("U19")
    invite = _invite_u17()
    assert EntreeSensations.objects.filter(joueur=invite).exists()
    avant = _client("prep_u19").get(f"/joueurs/{joueur.pk}/").content.decode()
    EntreeSensations.objects.filter(joueur=invite).delete()
    apres = _client("prep_u19").get(f"/joueurs/{joueur.pk}/").content.decode()
    jeton = r'name="csrfmiddlewaretoken" value="[^"]+"'
    assert re.sub(jeton, "", avant) == re.sub(jeton, "", apres)


def test_les_libelles_d_une_autre_categorie_ne_sont_pas_utilises(demo: None) -> None:
    # La démonstration partage des codes entre U17 et U19 : seul le libellé de la catégorie
    # de référence du joueur doit apparaître.
    Indicateur.objects.filter(categorie__code="U17", code="plaisir").update(libelle="LIBELLE-U17")
    page = _client("prep_u19").get(f"/joueurs/{_joueur('U19').pk}/").content.decode()
    assert "LIBELLE-U17" not in page


def test_un_joueur_sans_entree_a_une_fiche_sans_erreur() -> None:
    u19 = Categorie.objects.create(code="U19", libelle="U19")
    compte = get_user_model().objects.create_user("p19")
    Preparateur.objects.create(user=compte, categorie=u19)
    joueur = Joueur.objects.create(
        nom="Neuf",
        prenom="Test",
        date_naissance=datetime.date(2007, 3, 14),
        categorie_reference=u19,
    )
    client = Client()
    client.force_login(compte)
    with patch("suivi.views.fiche.aujourd_hui", return_value=FIN):
        reponse = client.get(f"/joueurs/{joueur.pk}/")
    assert reponse.status_code == 200
    assert "Aucune entrée de sensations" in reponse.content.decode()
