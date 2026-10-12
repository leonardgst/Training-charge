"""Configuration commune des tests.

Les tests unitaires tournent sans `.env` et sans base : les variables nécessaires aux
réglages sont posées ici, avant le chargement de Django.
"""

import os

import django
from django.test.utils import setup_test_environment

os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
os.environ.setdefault("DJANGO_SECRET_KEY", "cle-de-test-sans-valeur")
# Un `.env` de développement ne doit pas changer le comportement des tests.
os.environ["DJANGO_DEBUG"] = "false"

django.setup()
setup_test_environment()
