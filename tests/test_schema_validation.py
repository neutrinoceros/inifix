import pytest
from more_itertools import unzip

from inifix.io import dump, load
from inifix.validation import validate_inifile_schema

INVADLID_SCHEMAS, INVALID_SCHEMAS_IDS = unzip(
    (
        ({1: {"param": 1}}, "section_no_str"),
        ({"section": {"": 1}}, "empty_param_name"),
        ({"section": {"§": 1}}, "invalid_param_name-1"),
        ({"section": {"a§": 1}}, "invalid_param_name-2"),
        ({"section": {1: "one"}}, "param_name_no_str"),
        ({"section": [[1, 2], [3, 4]]}, "non_flat_section"),
        ({"section": {"param": [[1, 2], [3, 4]]}}, "nested_non_flat_sequence"),
        ({"section": {"subsection": {"subsubsection": 1}}}, "too_deep_nesting"),
    )
)


@pytest.fixture(params=INVADLID_SCHEMAS, ids=INVALID_SCHEMAS_IDS)
def invalid_conf(request):
    return request.param


def test_validate_known_files(inifile):
    conf = load(inifile)
    validate_inifile_schema(conf)


def test_dump_invalid_conf(invalid_conf, tmp_path):
    with pytest.raises(ValueError, match=r"^(Invalid schema)"):
        dump(invalid_conf, tmp_path / "save.ini")
