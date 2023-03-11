import pytest

import inifix
from inifix.io import _auto_cast

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


@pytest.mark.parametrize("s, expected", BASE_BOOLS)
def test_bool_cast(s, expected):
    assert _auto_cast(s) is expected


@pytest.mark.parametrize("s", ["tdsk", "1213", "Treu", "Flsae", "flkj"])
def test_bool_cast_invalid(s):
    assert type(_auto_cast(s)) is not bool


@pytest.mark.parametrize("s, expected", BASE_BOOLS)
def test_bool_cast_integration(s, expected, tmp_path):
    with open(tmp_path / "dummy.ini", "w") as fh:
        fh.write(f"dummy {s}")
    d = inifix.load(tmp_path / "dummy.ini")
    assert d == {"dummy": expected}


@pytest.mark.parametrize(
    "s, expected",
    [
        ("1.", 1),
        ("1.0", 1),
        ("1e3", 1000),
        ("+1.", 1),
        ("+1.0", 1),
        ("+1e3", 1000),
        ("-1.", -1),
        ("-1.0", -1),
        ("-1e3", -1000),
    ],
)
def test_float_cast(s, expected):
    res = _auto_cast(s)
    assert type(res) is type(expected)
    assert res == expected
