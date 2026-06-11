__all__ = [
    "assert_mapping_equal",
    "assert_scalar_equal",
]

from collections.abc import Mapping, Sequence
from math import isnan
from typing import TypeVar

K = TypeVar("K")
V = TypeVar("V")


def assert_scalar_equal(s1: V, s2: V, /) -> None:
    __tracebackhide__ = True
    assert type(s1) is type(s2)
    if type(s1) is float and type(s2) is float and isnan(s2):
        assert isnan(s1)
    else:
        assert s1 == s2


def assert_mapping_equal(m1: Mapping[K, V], m2: Mapping[K, V], /) -> None:
    __tracebackhide__ = True
    # note that key insertion order matters in this comparison
    assert list(m2.keys()) == list(m1.keys())
    for v1, v2 in zip(m1.values(), m2.values(), strict=True):
        match v1, v2:
            case Mapping(), Mapping():
                assert_mapping_equal(v1, v2)
            case Sequence(), Sequence():
                for s1, s2 in zip(v1, v2, strict=True):
                    assert_scalar_equal(s1, s2)
            case _:
                assert_scalar_equal(v1, v2)
