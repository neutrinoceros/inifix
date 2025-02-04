from math import isnan

import pytest
from hypothesis import given
from hypothesis import strategies as st

import inifix
from inifix._floatencoder import FloatEncoder
from inifix._io import _auto_cast_aggressive, _auto_cast_stable

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


@pytest.mark.parametrize("caster", [_auto_cast_stable, _auto_cast_aggressive])
@pytest.mark.parametrize("s, expected", BASE_BOOLS)
def test_bool_cast(caster, s, expected):
    assert caster(s) is expected


@pytest.mark.parametrize("caster", [_auto_cast_stable, _auto_cast_aggressive])
@pytest.mark.parametrize("s", ["tdsk", "1213", "Treu", "Flsae", "flkj"])
def test_bool_cast_invalid(caster, s):
    assert type(caster(s)) is not bool  # noqa: E721


@pytest.mark.parametrize("s, expected", BASE_BOOLS)
def test_bool_cast_integration(s, expected, tmp_path):
    with open(tmp_path / "dummy.ini", "w") as fh:
        fh.write(f"dummy {s}")
    d = inifix.load(tmp_path / "dummy.ini")
    assert d == {"dummy": expected}


@given(st.integers())
def test_unambiguous_int_cast_stable(i):
    s = str(i)
    res = _auto_cast_stable(s)
    assert res == i
    assert type(res) is int


# aggressively casting to float first leads to loss of precision beyond a threshold
@given(st.integers(min_value=-9_007_199_254_740_992, max_value=9_007_199_254_740_992))
def test_unambiguous_int_cast_aggressive(i):
    s = str(i)
    res = _auto_cast_aggressive(s)
    assert res == i
    assert type(res) is int


@pytest.mark.parametrize(
    "caster, expected_type",
    [
        (_auto_cast_stable, float),
        (_auto_cast_aggressive, int),
    ],
)
@given(st.integers())
def test_int_like_floats_casting(caster, expected_type, i):
    f = float(i)
    for s in (str(f), FloatEncoder.ENOTATION.encode(i)):
        res = caster(s)
        assert res == f
        assert type(res) is expected_type
        if expected_type is float:
            assert res.is_integer()


@pytest.mark.parametrize("caster", [_auto_cast_stable, _auto_cast_aggressive])
@given(st.floats())
def test_unambiguous_float_casting(caster, f):
    s = str(f)
    res = caster(s)
    if isnan(f):
        assert isnan(res)
    else:
        assert res == float(s)
    assert isinstance(res, int | float)
    if caster is _auto_cast_aggressive and f.is_integer():
        assert type(res) is int
    else:
        assert type(res) is float
