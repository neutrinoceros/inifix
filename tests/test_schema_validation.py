import pytest

from inifix.io import dump, load
from inifix.validation import validate_inifile_schema


def test_validate_known_files(inifile):
    conf = load(inifile)
    validate_inifile_schema(conf)


def test_dump_invalid_conf(invalid_conf, tmp_path):
    with pytest.raises(ValueError):
        dump(invalid_conf, tmp_path / "save.ini")
