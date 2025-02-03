from pathlib import Path

import pytest

from inifix import format_string
from inifix.format import iniformat

DATA_DIR = Path(__file__).parent / "data"


def test_depr():
    body = (DATA_DIR / "format-in.ini").read_text()
    s1 = format_string(body)
    with pytest.warns(
        DeprecationWarning,
        match="inifix.format.iniformat is deprecated",
    ):
        s2 = iniformat(body)
    assert s2 == s1
