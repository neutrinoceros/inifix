import difflib
import tempfile
from pathlib import Path

import pytest

from inifix.iniconf import InifixConf
from inifix.io import load


@pytest.mark.parametrize(
    "invalid_data", ["", "SingleToken", "[InvalidSectionName", "InvalidSection]"]
)
def test_tokenizer(invalid_data):
    with pytest.raises(ValueError):
        InifixConf.tokenize_line(invalid_data, filename="fake_filename", line_number=-1)


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

        text1 = save1.read_text().split("\n")
        text2 = save2.read_text().split("\n")

        diff = "".join(difflib.context_diff(text1, text2))
        assert not diff


@pytest.mark.parametrize(
    "data, expected",
    [
        ("""val content\n""", {"val": "content"}),
        ("""val 'content'\n""", {"val": "content"}),
        ("""val content"\n""", {"val": 'content"'}),
        ("""val "content\n""", {"val": '"content'}),
        ("""val content'\n""", {"val": "content'"}),
        ("""val 'content\n""", {"val": "'content"}),
        ("""val "content"\n""", {"val": "content"}),
        ("""val "content'"\n""", {"val": "content'"}),
        ("""val '"content"'\n""", {"val": '"content"'}),
        ("""val "'content'"\n""", {"val": "'content'"}),
        ("""val true\n""", {"val": True}),
        ("""val "true"\n""", {"val": "true"}),
        ("""val 'true'\n""", {"val": "true"}),
        ("""val false\n""", {"val": False}),
        ("""val "false"\n""", {"val": "false"}),
        ("""val 'false'\n""", {"val": "false"}),
        ("""val 1\n""", {"val": 1}),
        ("""val "1"\n""", {"val": "1"}),
        ("""val '1'\n""", {"val": "1"}),
        ("""val 1e2\n""", {"val": 100}),
        ("""val "1e2"\n""", {"val": "1e2"}),
        ("""val '1e2'\n""", {"val": "1e2"}),
    ],
)
def test_string_casting(data, expected, tmp_path):
    file = tmp_path / "test_file.ini"
    file.write_text(data)
    mapping = load(file)
    assert mapping == expected
