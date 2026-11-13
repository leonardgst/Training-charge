from django.apps import AppConfig


class SuiviConfig(AppConfig):
    name = "suivi"
    verbose_name = "Suivi de charge"

    def ready(self) -> None:
        # Un fichier de paramètres invalide interrompt le démarrage.
        from suivi.calculs import parametres

        parametres()

        from suivi.journal import configurer_journal_audit, masquer_le_jeton_des_journaux

        masquer_le_jeton_des_journaux()
        configurer_journal_audit()
