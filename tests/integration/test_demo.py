"""Données de démonstration (D3) : chargement depuis une base vide, invariants, reproductibilité."""

import datetime
import secrets
from collections.abc import Callable

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db.models import Count, F, Sum

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

pytestmark = pytest.mark.django_db(transaction=True)

FIN = datetime.date(2026, 10, 12)
JOURS = [FIN - datetime.timedelta(days=i) for i in range(56)]


@pytest.fixture
def charger() -> Callable[[], None]:
    mot_de_passe = secrets.token_urlsafe(12)

    def _charger() -> None:
        call_command("generer_demo", fin=FIN, mot_de_passe=mot_de_passe, verbosity=0)

    return _charger


def _signature() -> dict[str, object]:
    return {
        "joueurs": list(
            Joueur.objects.order_by("pk").values_list("nom", "prenom", "date_naissance", "actif")
        ),
        "seances": list(
            Seance.objects.order_by("pk").values_list("date", "type", "duree_min", "statut")
        ),
        "rpe": Participation.objects.aggregate(
            c=Sum("rpe_cardio"), m=Sum("rpe_musculaire"), t=Sum("rpe_teta"), n=Count("pk")
        ),
        "reponses": Reponse.objects.aggregate(v=Sum("valeur"), n=Count("pk")),
        "entrees": list(EntreeSensations.objects.order_by("pk").values_list("date")[:200]),
    }


def test_d3_chargement_depuis_une_base_vide(charger: Callable[[], None]) -> None:
    charger()
    assert set(Categorie.objects.values_list("code", flat=True)) == {"U19", "U17"}
    assert Joueur.objects.filter(categorie_reference__code="U19", actif=True).count() == 24
    assert Joueur.objects.filter(categorie_reference__code="U19", actif=False).count() == 1
    assert Joueur.objects.filter(categorie_reference__code="U17", actif=True).count() == 8
    assert Preparateur.objects.count() == 2
    assert get_user_model().objects.filter(is_superuser=True).count() == 1


def test_d3_effectifs_des_seances_deduits_du_calendrier(charger: Callable[[], None]) -> None:
    charger()
    attendu_u19 = sum(1 for jour in JOURS if jour.weekday() in {0, 1, 2, 3, 4, 5})
    attendu_u17 = sum(1 for jour in JOURS if jour.weekday() in {0, 2, 4})
    assert Seance.objects.filter(categorie_organisatrice__code="U19").count() == attendu_u19
    assert Seance.objects.filter(categorie_organisatrice__code="U17").count() == attendu_u17
    assert Seance.objects.filter(date__lt=min(JOURS)).count() == 0
    assert Seance.objects.filter(date__gt=FIN).count() == 0


def test_d3_seances_validees_completes_et_brouillon_incomplet(charger: Callable[[], None]) -> None:
    charger()
    validees = Participation.objects.filter(seance__statut="validee")
    assert validees.exists()
    assert not validees.filter(rpe_cardio__isnull=True).exists()
    assert not validees.filter(rpe_musculaire__isnull=True).exists()
    assert not validees.filter(rpe_teta__isnull=True).exists()
    brouillons = Seance.objects.filter(statut="brouillon")
    assert brouillons.count() == 1
    assert Participation.objects.filter(seance__in=brouillons, rpe_cardio__isnull=True).exists()


def test_d3_joueurs_invites_et_joueur_archive(charger: Callable[[], None]) -> None:
    charger()
    invites = Participation.objects.exclude(
        joueur__categorie_reference=F("seance__categorie_organisatrice")
    )
    assert invites.exists()
    assert set(invites.values_list("seance__categorie_organisatrice__code", flat=True)) == {"U19"}
    archive = Joueur.objects.get(actif=False)
    assert archive.participations.exists()
    # parti en milieu de période : présent au début, absent des deux dernières semaines
    assert archive.participations.filter(
        seance__date__lt=FIN - datetime.timedelta(days=28)
    ).exists()
    assert not archive.participations.filter(
        seance__date__gt=FIN - datetime.timedelta(days=14)
    ).exists()
    assert not archive.entrees.filter(date__gt=FIN - datetime.timedelta(days=14)).exists()


def test_d3_sensations_conformes_aux_indicateurs_et_aux_jours(charger: Callable[[], None]) -> None:
    charger()
    u19 = Indicateur.objects.filter(categorie__code="U19")
    assert u19.count() == 9
    assert set(u19.filter(inclus_score=False).values_list("code", flat=True)) == {
        "heure_coucher",
        "heure_lever",
    }
    for entree in EntreeSensations.objects.filter(joueur__categorie_reference__code="U17"):
        assert entree.date.weekday() in {0, 1, 2, 3, 4}
    assert EntreeSensations.objects.filter(joueur__categorie_reference__code="U19").exists()
    assert not Reponse.objects.filter(
        indicateur__sens="aucun", indicateur__inclus_score=True
    ).exists()


def test_d3_un_joueur_a_surveiller_se_degrade_en_fin_de_periode(
    charger: Callable[[], None],
) -> None:
    charger()
    joueur = (
        Joueur.objects.filter(categorie_reference__code="U19", actif=True).order_by("pk").first()
    )
    assert joueur is not None

    def fatigue_moyenne(debut: int, fin: int) -> float:
        valeurs = Reponse.objects.filter(
            entree__joueur=joueur,
            indicateur__code="fatigue",
            entree__date__gt=FIN - datetime.timedelta(days=debut),
            entree__date__lte=FIN - datetime.timedelta(days=fin),
        ).values_list("valeur", flat=True)
        return sum(valeurs) / len(valeurs)

    assert fatigue_moyenne(10, 0) > fatigue_moyenne(40, 10) + 1


def test_d3_deux_chargements_donnent_les_memes_donnees(charger: Callable[[], None]) -> None:
    charger()
    premiere = _signature()
    call_command("flush", interactive=False, verbosity=0)
    assert not Joueur.objects.exists()
    charger()
    assert _signature() == premiere


def test_d3_refus_sur_une_base_qui_contient_deja_des_donnees(charger: Callable[[], None]) -> None:
    charger()
    avant = Joueur.objects.count()
    with pytest.raises(CommandError, match="déjà des données"):
        charger()
    assert Joueur.objects.count() == avant


def test_d3_date_de_fin_par_defaut_est_la_date_du_jour_du_projet(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "suivi.management.commands.generer_demo.aujourd_hui", lambda: datetime.date(2026, 3, 4)
    )
    call_command("generer_demo", mot_de_passe=secrets.token_urlsafe(12), verbosity=0)
    assert Seance.objects.order_by("-date").first().date <= datetime.date(2026, 3, 4)  # type: ignore[union-attr]
    assert Seance.objects.filter(date__gte=datetime.date(2026, 3, 1)).exists()


def test_d3_les_comptes_de_demonstration_ont_les_bons_droits(charger: Callable[[], None]) -> None:
    charger()
    utilisateurs = get_user_model().objects
    admin = utilisateurs.get(username="admin_demo")
    assert admin.is_superuser and admin.is_staff
    for nom in ("prep_u19", "prep_u17"):
        compte = utilisateurs.get(username=nom)
        assert not compte.is_staff and not compte.is_superuser
        assert compte.preparateur.categorie.code == nom.removeprefix("prep_").upper()
