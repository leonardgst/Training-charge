"""Cas fictif écrit à la volée pour tester le harnais lui-même.

Il n'a aucune valeur de référence : ses chiffres servent seulement à exercer la lecture,
la validation, le chargement en base et la comparaison.
"""

from pathlib import Path

FICHIERS = {
    "cas.toml": (
        'description = "cas de test du harnais"\n\n[parametres]\nfacteur_echelle_charge = 1.0\n'
    ),
    "joueurs.csv": "joueur,categorie\nJ1,U19\nJ2,U19\n",
    "seances.csv": (
        "id,date,categorie,type,duree_min,statut\n"
        "S1,2026-01-05,U19,foot,60,validee\n"
        "S2,2026-01-06,U19,foot,45,brouillon\n"
    ),
    "participations.csv": (
        "seance_id,joueur,rpe_cardio,rpe_musculaire,rpe_teta\nS1,J1,5,6,4\nS1,J2,7,7,7\nS2,J1,3,,\n"
    ),
    "indicateurs.csv": (
        "categorie,code,type,borne_min,borne_max,sens,poids,inclus_score\n"
        "U19,fatigue,note,1,5,bas_bon,1.00,true\n"
    ),
    "reponses.csv": "joueur,date,indicateur,valeur\nJ1,2026-01-05,fatigue,3\n",
    "attendu.csv": (
        "joueur,date,grandeur,valeur,etat\n"
        "J1,2026-01-05,charge_jour,300.0,ok\n"
        "J1,2026-01-05,intensite,,historique_insuffisant\n"
    ),
}


def ecrire_cas(dossier: Path, **remplacements: str | None) -> Path:
    """Écrit le cas fictif ; `remplacements` change ou supprime (None) un fichier."""
    dossier.mkdir(parents=True, exist_ok=True)
    for nom, contenu in {**FICHIERS, **remplacements}.items():
        chemin = dossier / nom
        if contenu is None:
            chemin.unlink(missing_ok=True)
        else:
            chemin.write_text(contenu, encoding="utf-8")
    return dossier
