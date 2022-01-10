import pytest

import inifix
from inifix.io import bool_caster

BASE_BOOLS = [
    ("True", True),
    ("true", True),
    ("T", True),
    ("t", True),
    ("False", False),
    ("false", False),
    ("F", False),
    ("f", False),
]


@pytest.mark.parametrize("s, expected", BASE_BOOLS)
def test_bool_cast(s, expected):
    assert bool_caster(s) is expected


@pytest.mark.parametrize("s", ["tdsk", "1213", "Treu", "Flsae", "flkj"])
def test_bool_cast_invalid(s):
    with pytest.raises(ValueError):
        bool_caster(s)


@pytest.mark.parametrize("s, expected", BASE_BOOLS)
def test_bool_cast_integration(s, expected, tmp_path):
    with open(tmp_path / "dummy.ini", "w") as fh:
        fh.write(f"dummy {s}")
    d = inifix.load(tmp_path / "dummy.ini")
    assert d == {"dummy": expected}
