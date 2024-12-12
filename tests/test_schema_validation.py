import pytest

from inifix.io import dump, load
from inifix.validation import validate_inifile_schema


def test_validate_known_files(inifile):
    conf = load(inifile)
    # implicit form
    validate_inifile_schema(conf)

    # explicit form
    validate_inifile_schema(conf, sections="allow")


def test_validate_known_files_with_sections(inifile_with_sections):
    conf = load(inifile_with_sections)
    validate_inifile_schema(conf, sections="forbid")
    with pytest.raises(
        ValueError,
        match=(
            "Invalid schema: sections were explicitly required, "
            "but the following key/value pair was found outside of "
            "any section"
        ),
    ):
        validate_inifile_schema(conf, sections="require")


def test_validate_known_files_without_sections(inifile_without_sections):
    conf = load(inifile_without_sections)
    validate_inifile_schema(conf, sections="require")
    with pytest.raises(
        ValueError,
        match=(
            "Invalid schema: sections were explicitly forbidden, "
            "but one was found under key"
        ),
    ):
        validate_inifile_schema(conf, sections="forbid")


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


def test_unknown_sections_value():
    with pytest.raises(TypeError):
        validate_inifile_schema({}, sections="unknown-value")
