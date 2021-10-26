import re

import pytest

from inifix._deprecation import future_positional_only


def test_future_positional_only():

    msg = re.escape(
        "using the 'b' argument as keyword (on position 1) "
        "is deprecated and will stop working in a future release. "
        "Pass the argument as positional to supress this warning."
    )

    @future_positional_only({1: "b"})
    def dummy_func(a, b):
        pass

    with pytest.warns(FutureWarning, match=msg):
        dummy_func(1, b=2)

    with pytest.warns(FutureWarning, match=msg):
        dummy_func(a=1, b=2)

    # should not raise a warning
    dummy_func(1, 2)
