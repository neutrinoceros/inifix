import pytest

import inifix
from inifix.io import _auto_cast_agressive, _auto_cast_stable

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


@pytest.mark.parametrize("caster", [_auto_cast_stable, _auto_cast_agressive])
@pytest.mark.parametrize("s, expected", BASE_BOOLS)
def test_bool_cast(caster, s, expected):
    assert caster(s) is expected


@pytest.mark.parametrize("caster", [_auto_cast_stable, _auto_cast_agressive])
@pytest.mark.parametrize("s", ["tdsk", "1213", "Treu", "Flsae", "flkj"])
def test_bool_cast_invalid(caster, s):
    assert type(caster(s)) is not bool  # noqa: E721


@pytest.mark.parametrize("s, expected", BASE_BOOLS)
def test_bool_cast_integration(s, expected, tmp_path):
    with open(tmp_path / "dummy.ini", "w") as fh:
        fh.write(f"dummy {s}")
    d = inifix.load(tmp_path / "dummy.ini")
    assert d == {"dummy": expected}


@pytest.mark.parametrize("caster", [_auto_cast_stable, _auto_cast_agressive])
@pytest.mark.parametrize(
    "s, expected",
    [("0", 0), ("123", 123), ("-1", -1)],
)
def test_unambiguous_int(caster, s, expected):
    res = caster(s)
    assert res == expected
    assert type(res) is int


@pytest.mark.parametrize(
    "caster, expected_type",
    [
        (_auto_cast_stable, float),
        (_auto_cast_agressive, int),
    ],
)
@pytest.mark.parametrize(
    "s",
    ["0.", "1.", "1.0", "1e3", "+1.", "+1.0", "+1e3", "-1.", "-1.0", "-1e3"],
)
def test_int_like_casting(caster, expected_type, s):
    res = caster(s)
    assert res == float(s)
    assert type(res) is expected_type
    if expected_type is float:
        assert res.is_integer()


@pytest.mark.parametrize("caster", [_auto_cast_stable, _auto_cast_agressive])
@pytest.mark.parametrize(
    "s",
    ["0.1", "1.2", "3.56789e2"],
)
def test_unambiguous_float_casting(caster, s):
    res = caster(s)
    assert res == float(s)
    assert type(res) is float
