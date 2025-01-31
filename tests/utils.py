from math import isnan


def assert_item_equal(i1: object, i2: object) -> None:
    __tracebackhide__ = True
    assert type(i1) is type(i2)
    if type(i1) is float and type(i2) is float and isnan(i2):
        assert isnan(i1)
    else:
        assert i1 == i2


def assert_dict_equal(d1: dict, d2: dict) -> None:
    __tracebackhide__ = True
    # note that key insertion order matters in this comparison
    assert list(d2.keys()) == list(d1.keys())
    for v1, v2 in zip(d1.values(), d2.values(), strict=True):
        assert type(v1) is type(v2)
        if isinstance(v1, dict):
            assert_dict_equal(v1, v2)
        elif isinstance(v1, list):
            for i1, i2 in zip(v1, v2, strict=True):
                assert_item_equal(i1, i2)
        else:
            assert_item_equal(v1, v2)
