import pytest

import inifix
from inifix.io import _RE_CASTERS

BASE_BOOLS = [
    ("True", True),
    ("true", True),
    ("Yes", True),
    ("yes", True),
    ("False", False),
    ("false", False),
    ("No", False),
    ("no", False),
]


def autocast(v):
    for regexp, caster in _RE_CASTERS:
        if regexp.fullmatch(v):
            return caster(v)


@pytest.mark.parametrize("s, expected", BASE_BOOLS)
def test_bool_cast(s, expected):
    assert autocast(s) is expected


@pytest.mark.parametrize("s", ["tdsk", "1213", "Treu", "Flsae", "flkj"])
def test_bool_cast_invalid(s):
    assert type(autocast(s)) is not bool


@pytest.mark.parametrize("s, expected", BASE_BOOLS)
def test_bool_cast_integration(s, expected, tmp_path):
    with open(tmp_path / "dummy.ini", "w") as fh:
        fh.write(f"dummy {s}")
    d = inifix.load(tmp_path / "dummy.ini")
    assert d == {"dummy": expected}
