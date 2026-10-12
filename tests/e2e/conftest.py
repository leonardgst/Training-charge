"""Fixtures de bout en bout : serveur de test de `pytest-django` et Chromium.

`DJANGO_ALLOW_ASYNC_UNSAFE` n'est activé qu'ici, pour Playwright (CLAUDE.md, section 10).
"""

import os

os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")
