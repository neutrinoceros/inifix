import difflib
import tempfile
from pathlib import Path

import pytest

from inifix.iniconf import IniConf


@pytest.mark.parametrize(
    "invalid_data", ["", "SingleToken", "[InvalidSectionName", "InvalidSection]"]
)
def test_tokenizer(invalid_data):
    with pytest.raises(ValueError):
        IniConf.tokenize_line(invalid_data)


def test_unit_read(inifile):
    IniConf(inifile)


def test_oop_write(inifile):
    conf = IniConf(inifile)
    with tempfile.TemporaryFile(mode="wt") as tmpfile:
        conf.write(tmpfile)


def test_idempotent_io(inifile):
    data0 = IniConf(inifile)
    with tempfile.TemporaryDirectory() as tmpdir:
        save1 = Path(tmpdir) / "save1"
        save2 = Path(tmpdir) / "save2"
        data0.write(save1)
        data1 = IniConf(save1)
        data1.write(save2)

        text1 = open(save1, "r").readlines()
        text2 = open(save2, "r").readlines()

        diff = "".join(difflib.context_diff(text1, text2))
        assert not diff
