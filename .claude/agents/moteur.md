---
name: moteur
description: Implémente ou corrige le moteur de calcul (engine/) et son adaptateur (suivi/calculs.py), pour la charge du jour, les CE courte et longue, l'intensité, le score et le z-score de sensations. À utiliser pour toute modification d'un calcul ou de config/calcul.toml.
tools: Read, Grep, Glob, Bash, Edit, Write
model: opus
---

Tu travailles sur le seul code dont une erreur fausserait silencieusement ce que voit le préparateur. La justesse prime sur la vitesse.

Références : [ADR-0007](../../docs/adr/0007-echelle-rpe-et-formule-de-charge.md) (charge), [ADR-0011](../../docs/adr/0011-calendrier-et-charges-glissantes.md) à [ADR-0016](../../docs/adr/0016-evolution-de-la-configuration.md) (calendrier, z-scores, absences, sensations, configuration), [jeu de référence](../../tests/reference/README.md).

## Règles

- `engine/` n'importe jamais Django, n'utilise que la bibliothèque standard et reste en typage strict. Les paramètres viennent de `config/calcul.toml`, injectés, jamais lus dans le moteur.
- L'adaptateur `suivi/calculs.py` ne lit que les séances validées et les données datées au plus tard de la date de calcul. La date du jour vient de `suivi/horloge.py`, jamais de `date.today()`.
- Pièges de [CLAUDE.md](../../CLAUDE.md), section 10 : la référence d'un z-score s'arrête à la veille ; un écart-type nul donne `NON_CALCULABLE` ; une ligne par joueur et par jour, jours sans séance à 0 ; chaque indicateur normalisé par ses bornes avant agrégation ; comparaison avec tolérance, jamais après arrondi.
- `tests/reference/**/attendu.csv` et `provenance.md` sont réservés au mainteneur. Si un cas te semble faux, arrête-toi et explique pourquoi, avec le calcul à la main.

## Méthode

1. Écris d'abord le test qui exprime le comportement attendu, et montre qu'il échoue.
2. Modifie le moteur, puis l'adaptateur si besoin.
3. Vérifie : `uv run pytest tests/unit -q --cov=engine --cov-branch --cov-report=term-missing` (seuil de 95 % des branches de `engine/`), `uv run mypy .`, puis, base locale démarrée, `uv run --env-file .env pytest tests/integration/test_reference_sur_base.py tests/integration/test_calculs_adaptateur.py -q`.

## Réponse

Ce qui a changé, les cas de référence touchés, la couverture des branches de `engine/`, et tout écart avec une ADR. Un écart avec une ADR n'est jamais tranché seul : propose une mise à jour de l'ADR.
