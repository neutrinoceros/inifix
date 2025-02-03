from math import isnan

import pytest
from hypothesis import example, given
from hypothesis import strategies as st

from inifix._enotation import Enotation


@pytest.mark.parametrize(
    "input, expected",
    [
        ("1e-00", "1e0"),
        ("1e-01", "1e-1"),
        ("1e+01", "1e1"),
        ("1e+10", "1e10"),
        ("1.000e+00", "1e0"),
        ("1.100e+00", "1.1e0"),
    ],
)
def test_simplify(input, expected):
    assert Enotation._simplify(input) == expected


@pytest.mark.parametrize(
    "input, expected",
    [
        (1, "1e0"),
        (0.000_000_1, "1e-7"),
        (10_000_000, "1e7"),
        (156_000, "1.56e5"),
        (0.0056, "5.6e-3"),
        (3.141592653589793, "3.141592653589793e0"),
        (1e-15, "1e-15"),
        (0.0, "0e0"),
        (0, "0e0"),
    ],
)
def test_always_encode(input, expected):
    assert Enotation.ALWAYS.encode(input) == expected


@pytest.mark.parametrize(
    "input, expected",
    [
        (1, "1.0"),
        (0.000_000_1, "1e-7"),
        (10_000_000, "1e7"),
        (156_000, "1.56e5"),
        (0.0056, "0.0056"),
        (3.141592653589793, "3.141592653589793"),
        (1e-15, "1e-15"),
        (0.0, "0.0"),
        (0, "0.0"),
    ],
)
def test_only_shorter_encode(input, expected):
    assert Enotation.ONLY_SHORTER.encode(input) == expected


# for reliable coverage, include a mandatory example for
# each branch in the test
@example(100.0)  # len('1e2') < len('100.0')
@example(1.0)  # len('1e0') == len('1.0')
@example(0.5)  # len('5e-1') > len('0.5')
@example(float("nan"))
@given(st.floats())
def test_strategies_comparison(r):
    s0 = str(r)
    s1 = Enotation.ALWAYS.encode(r)
    s2 = Enotation.ONLY_SHORTER.encode(r)

    if isnan(r):
        assert isnan(float(s1))
        assert isnan(float(s2))
    else:
        assert float(s1) == r
        assert float(s2) == r

    assert len(s2) <= len(s1)
    assert len(s2) <= len(s0)
    assert s2 in (s1, s0)

    if len(s1) < len(s0):
        assert s2 == s1
    else:
        assert s2 == s0
