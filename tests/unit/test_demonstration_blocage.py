"""Test volontairement en échec : démontre qu'une PR dont un test échoue ne peut pas être fusionnée.

Cette branche ne doit jamais être fusionnée ; la PR est fermée après la démonstration.
"""


def test_en_echec_volontaire() -> None:
    assert 1 + 1 == 3
