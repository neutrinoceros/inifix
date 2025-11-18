import sys

import pytest
from pytest import RaisesExc, RaisesGroup

from inifix import dump, dumps, load, loads, validate_inifile_schema

from .utils import assert_dict_equal

if sys.version_info < (3, 11):
    from exceptiongroup import ExceptionGroup


def test_validate_known_files(inifile):
    conf = load(inifile)
    # implicit form
    validate_inifile_schema(conf)

    # explicit form
    validate_inifile_schema(conf, sections="allow")


def test_validate_known_files_without_sections(inifile_without_sections, tmp_path):
    conf1 = load(inifile_without_sections)
    validate_inifile_schema(conf1, sections="forbid")

    expected_msg = (
        "Invalid schema: sections were explicitly required, "
        "but the following key/value pair was found outside of "
        "any section"
    )
    with pytest.raises(ValueError, match=expected_msg):
        validate_inifile_schema(conf1, sections="require")

    with pytest.raises(ValueError, match=expected_msg):
        load(inifile_without_sections, sections="require")

    # check that sections=... doesn't have any effect when combined with skip_validation=True
    conf2 = load(inifile_without_sections, sections="require", skip_validation=True)
    assert_dict_equal(conf2, conf1)

    save_file = tmp_path / "test"
    with pytest.raises(ValueError, match=expected_msg):
        dump(conf1, save_file, sections="require")
    assert not save_file.exists()

    dump(conf1, save_file, sections="require", skip_validation=True)
    assert save_file.is_file()

    with pytest.raises(ValueError, match=expected_msg):
        dumps(conf1, sections="require")

    s = dumps(conf1, sections="require", skip_validation=True)

    conf3 = loads(s)
    assert_dict_equal(conf3, conf1)
    with pytest.raises(ValueError, match=expected_msg):
        loads(s, sections="require")

    conf4 = loads(s, sections="require", skip_validation=True)
    assert_dict_equal(conf4, conf3)


def test_validate_known_files_with_sections(inifile_with_sections, tmp_path):
    conf1 = load(inifile_with_sections)
    validate_inifile_schema(conf1, sections="require")
    expected_msg = (
        "Invalid schema: sections were explicitly forbidden, "
        "but one was found under key"
    )
    with pytest.raises(ValueError, match=expected_msg):
        validate_inifile_schema(conf1, sections="forbid")

    with pytest.raises(ValueError, match=expected_msg):
        load(inifile_with_sections, sections="forbid")

    # check that sections=... doesn't have any effect when combined with skip_validation=True
    conf2 = load(inifile_with_sections, sections="forbid", skip_validation=True)
    assert_dict_equal(conf2, conf1)

    save_file = tmp_path / "test"
    with pytest.raises(ValueError, match=expected_msg):
        dump(conf1, save_file, sections="forbid")
    assert not save_file.exists()

    dump(conf1, save_file, sections="forbid", skip_validation=True)
    assert save_file.is_file()

    with pytest.raises(ValueError, match=expected_msg):
        dumps(conf1, sections="forbid")

    s = dumps(conf1, sections="forbid", skip_validation=True)

    conf3 = loads(s)
    assert_dict_equal(conf3, conf1)
    with pytest.raises(ValueError, match=expected_msg):
        loads(s, sections="forbid")

    conf4 = loads(s, sections="forbid", skip_validation=True)
    assert_dict_equal(conf4, conf3)


@pytest.mark.parametrize(
    "invalid_conf, match",
    [
        pytest.param({1: {"param": 1}}, r"^Invalid schema", id="section_no_str"),
        pytest.param(
            {"section": {"": 1}}, r"^Found an empty str as key", id="empty_param_name"
        ),
        pytest.param(
            {"section": {"§": 1}},
            r"^Found key '§', expected only alphanumeric characters",
            id="invalid_param_name-1",
        ),
        pytest.param(
            {"section": {"a§": 1}},
            r"^Found key 'a§', expected only alphanumeric characters",
            id="invalid_param_name-2",
        ),
        pytest.param(
            {"section": {1: "one"}},
            r"^Found key 1 with type int\. Expected a str$",
            id="param_name_no_str",
        ),
        pytest.param(
            {"section": [[1, 2], [3, 4]]},
            (
                r"^Key 'section' is associated to values \[\[1, 2\], \[3, 4\]\] "
                r"with types \[list, list\], respectively\. "
                r"Expected only int, float, bool and str values$"
            ),
            id="non_flat_section",
        ),
        pytest.param(
            {"section": {"param": [[1, 2], [3, 4]]}},
            (
                r"^Key 'param' is associated to values \[\[1, 2\], \[3, 4\]\] "
                r"with types \[list, list\], respectively\. "
                r"Expected only int, float, bool and str values$"
            ),
            id="nested_non_flat_sequence",
        ),
        pytest.param(
            {"section": {"subsection": {"subsubsection": 1}}},
            (
                r"^Key 'subsection' is associated to value \{'subsubsection': 1\} "
                r"with type dict\. "
                r"Expected an int, float, bool, str, or list of these types$"
            ),
            id="too_deep_nesting",
        ),
    ],
)
def test_dump_invalid_conf(invalid_conf, match, tmp_path):
    with RaisesGroup(
        RaisesExc(ValueError, match=match),
        allow_unwrapped=True,
        flatten_subgroups=True,
    ) as excinfo:
        dump(invalid_conf, tmp_path / "save.ini")
    if isinstance(excinfo.value, ExceptionGroup):
        assert RaisesGroup(
            ExceptionGroup,
            match=r"^Invalid schema",
        ).matches(excinfo.value)


def test_unknown_sections_value():
    with pytest.raises(TypeError):
        validate_inifile_schema(
            {},
            sections="unknown-value",  # type: ignore
        )
