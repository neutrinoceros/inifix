import pytest

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
