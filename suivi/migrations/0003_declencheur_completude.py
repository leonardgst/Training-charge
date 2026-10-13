"""Déclencheurs de complétude : aucune participation incomplète dans une séance validée.

Règle qui traverse deux tables (ADR-0008), donc portée par la base. Les fonctions
s'exécutent avec les droits de l'appelant (pas de `SECURITY DEFINER`).
"""

from django.db import migrations

CREER = """
CREATE FUNCTION suivi_participation_complete() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF (NEW.rpe_cardio IS NULL OR NEW.rpe_musculaire IS NULL OR NEW.rpe_teta IS NULL)
     AND EXISTS (SELECT 1 FROM suivi_seance WHERE id = NEW.seance_id AND statut = 'validee')
  THEN
    RAISE EXCEPTION 'participation incomplète dans une séance validée'
      USING ERRCODE = 'check_violation';
  END IF;
  RETURN NEW;
END $$;

CREATE TRIGGER suivi_participation_complete
  BEFORE INSERT OR UPDATE ON suivi_participation
  FOR EACH ROW EXECUTE FUNCTION suivi_participation_complete();

CREATE FUNCTION suivi_validation_seance() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM suivi_participation
    WHERE seance_id = NEW.id
      AND (rpe_cardio IS NULL OR rpe_musculaire IS NULL OR rpe_teta IS NULL)
  ) THEN
    RAISE EXCEPTION 'séance non validable : participations incomplètes'
      USING ERRCODE = 'check_violation';
  END IF;
  RETURN NEW;
END $$;

CREATE TRIGGER suivi_validation_seance
  BEFORE INSERT OR UPDATE OF statut ON suivi_seance
  FOR EACH ROW WHEN (NEW.statut = 'validee')
  EXECUTE FUNCTION suivi_validation_seance();
"""

SUPPRIMER = """
DROP TRIGGER suivi_validation_seance ON suivi_seance;
DROP FUNCTION suivi_validation_seance();
DROP TRIGGER suivi_participation_complete ON suivi_participation;
DROP FUNCTION suivi_participation_complete();
"""


class Migration(migrations.Migration):
    dependencies = [("suivi", "0002_seances_participations")]
    operations = [migrations.RunSQL(CREER, reverse_sql=SUPPRIMER)]
