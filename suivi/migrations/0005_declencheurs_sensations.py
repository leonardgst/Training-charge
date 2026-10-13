"""Déclencheurs des sensations : valeur dans les bornes, échelle figée (ADR-0010, ADR-0016).

Règles qui traversent deux tables, donc portées par la base. Les fonctions s'exécutent
avec les droits de l'appelant (pas de `SECURITY DEFINER`).
"""

from django.db import migrations

CREER = """
CREATE FUNCTION suivi_reponse_dans_les_bornes() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM suivi_indicateur
    WHERE id = NEW.indicateur_id AND NEW.valeur BETWEEN borne_min AND borne_max
  ) THEN
    RAISE EXCEPTION 'valeur hors des bornes de l''indicateur'
      USING ERRCODE = 'check_violation';
  END IF;
  RETURN NEW;
END $$;

CREATE TRIGGER suivi_reponse_dans_les_bornes
  BEFORE INSERT OR UPDATE ON suivi_reponse
  FOR EACH ROW EXECUTE FUNCTION suivi_reponse_dans_les_bornes();

CREATE FUNCTION suivi_echelle_figee() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF (NEW.type, NEW.borne_min, NEW.borne_max) IS DISTINCT FROM
     (OLD.type, OLD.borne_min, OLD.borne_max)
     AND EXISTS (SELECT 1 FROM suivi_reponse WHERE indicateur_id = OLD.id)
  THEN
    RAISE EXCEPTION 'échelle figée : des réponses existent pour cet indicateur'
      USING ERRCODE = 'check_violation';
  END IF;
  RETURN NEW;
END $$;

CREATE TRIGGER suivi_echelle_figee
  BEFORE UPDATE OF type, borne_min, borne_max ON suivi_indicateur
  FOR EACH ROW EXECUTE FUNCTION suivi_echelle_figee();
"""

SUPPRIMER = """
DROP TRIGGER suivi_echelle_figee ON suivi_indicateur;
DROP FUNCTION suivi_echelle_figee();
DROP TRIGGER suivi_reponse_dans_les_bornes ON suivi_reponse;
DROP FUNCTION suivi_reponse_dans_les_bornes();
"""


class Migration(migrations.Migration):
    dependencies = [("suivi", "0004_indicateurs_sensations")]
    operations = [migrations.RunSQL(CREER, reverse_sql=SUPPRIMER)]
