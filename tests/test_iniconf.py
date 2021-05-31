import difflib
import tempfile
from pathlib import Path

import pytest

from inifix.iniconf import InifixConf


@pytest.mark.parametrize(
    "invalid_data", ["", "SingleToken", "[InvalidSectionName", "InvalidSection]"]
)
def test_tokenizer(invalid_data):
    with pytest.raises(ValueError):
        InifixConf.tokenize_line(invalid_data, line_number=-1)


def test_unit_read(inifile):
    InifixConf(inifile)


def test_oop_write(inifile):
    conf = InifixConf(inifile)
    with tempfile.TemporaryFile(mode="wt") as tmpfile:
        conf.write(tmpfile)


def test_idempotent_io(inifile):
    data0 = InifixConf(inifile)
    with tempfile.TemporaryDirectory() as tmpdir:
        save1 = Path(tmpdir) / "save1"
        save2 = Path(tmpdir) / "save2"
        data0.write(save1)
        data1 = InifixConf(save1)
        data1.write(save2)

        text1 = open(save1).readlines()
        text2 = open(save2).readlines()

        diff = "".join(difflib.context_diff(text1, text2))
        assert not diff
