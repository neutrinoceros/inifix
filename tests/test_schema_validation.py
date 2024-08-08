import pytest

from inifix.io import dump, load
from inifix.validation import validate_inifile_schema


def test_validate_known_files(inifile):
    conf = load(inifile)
    validate_inifile_schema(conf)


@pytest.mark.parametrize(
    "invalid_conf",
    [
        pytest.param({1: {"param": 1}}, id="section_no_str"),
        pytest.param({"section": {"": 1}}, id="empty_param_name"),
        pytest.param({"section": {"§": 1}}, id="invalid_param_name-1"),
        pytest.param({"section": {"a§": 1}}, id="invalid_param_name-2"),
        pytest.param({"section": {1: "one"}}, id="param_name_no_str"),
        pytest.param({"section": [[1, 2], [3, 4]]}, id="non_flat_section"),
        pytest.param(
            {"section": {"param": [[1, 2], [3, 4]]}}, id="nested_non_flat_sequence"
        ),
        pytest.param(
            {"section": {"subsection": {"subsubsection": 1}}}, id="too_deep_nesting"
        ),
    ],
)
def test_dump_invalid_conf(invalid_conf, tmp_path):
    with pytest.raises(ValueError, match=r"^(Invalid schema)"):
        dump(invalid_conf, tmp_path / "save.ini")
