from math import isnan
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

import inifix
from inifix._floatencoder import FloatEncoder
from inifix._io import auto_cast_aggressive, auto_cast_stable
from inifix._typing import CasterFunction

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


@pytest.mark.parametrize("caster", [auto_cast_stable, auto_cast_aggressive])
@pytest.mark.parametrize("s, expected", BASE_BOOLS)
def test_bool_cast(caster: CasterFunction, s: str, expected: bool) -> None:
    assert caster(s) is expected


@pytest.mark.parametrize("caster", [auto_cast_stable, auto_cast_aggressive])
@pytest.mark.parametrize("s", ["tdsk", "1213", "Treu", "Flsae", "flkj"])
def test_bool_cast_invalid(caster: CasterFunction, s: str) -> None:
    assert type(caster(s)) is not bool  # noqa: E721


@pytest.mark.parametrize("s, expected", BASE_BOOLS)
def test_bool_cast_integration(s: str, expected: bool, tmp_path: Path) -> None:
    with open(tmp_path / "dummy.ini", "w", encoding="utf-8") as fh:
        fh.write(f"dummy {s}")
    d = inifix.load(tmp_path / "dummy.ini")
    assert d == {"dummy": expected}


@given(st.integers())
def test_unambiguous_int_cast_stable(i: int) -> None:
    s = str(i)
    res = auto_cast_stable(s)
    assert res == i
    assert type(res) is int


# aggressively casting to float first leads to loss of precision beyond a threshold
@given(st.integers(min_value=-9_007_199_254_740_992, max_value=9_007_199_254_740_992))
def test_unambiguous_int_cast_aggressive(i: int) -> None:
    s = str(i)
    res = auto_cast_aggressive(s)
    assert res == i
    assert type(res) is int


@pytest.mark.parametrize(
    "caster, expected_type",
    [
        (auto_cast_stable, float),
        (auto_cast_aggressive, int),
    ],
)
@given(st.integers())
def test_int_like_floats_casting(
    caster: CasterFunction, expected_type: type, i: int
) -> None:
    f = float(i)
    for s in (str(f), FloatEncoder.ENOTATION.encode(i)):
        res = caster(s)
        assert res == f
        assert type(res) is expected_type
        if type(res) is float:
            assert res.is_integer()


@pytest.mark.parametrize("caster", [auto_cast_stable, auto_cast_aggressive])
@given(st.floats())
def test_unambiguous_float_casting(caster: CasterFunction, f: float) -> None:
    s = str(f)
    res = caster(s)
    assert isinstance(res, int | float)
    if isnan(f):
        if not isinstance(res, float):
            raise AssertionError
        assert isnan(res)
    else:
        assert res == float(s)
    if caster is auto_cast_aggressive and f.is_integer():
        assert type(res) is int
    else:
        assert type(res) is float
