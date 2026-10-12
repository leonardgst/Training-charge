"""Configuration commune des tests.

Les tests unitaires tournent sans `.env` et sans base : les variables nécessaires aux
réglages sont posées ici, avant que `pytest-django` ne charge Django.
"""

import os

os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
os.environ.setdefault("DJANGO_SECRET_KEY", "cle-de-test-sans-valeur")
# Un `.env` de développement ne doit pas changer le comportement des tests.
os.environ["DJANGO_DEBUG"] = "false"

import django  # noqa: E402

django.setup()
