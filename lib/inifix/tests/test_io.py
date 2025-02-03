import difflib
import os
import re
import sys
import tempfile
from io import BytesIO
from pathlib import Path
from stat import S_IREAD

import pytest
from hypothesis import example, given
from hypothesis import strategies as st

from inifix import dump, dumps, load, loads
from inifix._io import (
    ALL_BOOL_STRINGS,
    FALSY_STRINGS,
    TRUTHY_STRINGS,
    _auto_cast_stable,
    _tokenize_line,
    _validate_section_item,
)

from .utils import assert_dict_equal


@pytest.mark.parametrize(
    "invalid_data", ["", "SingleToken", "[InvalidSectionName", "InvalidSection]"]
)
def test_tokenizer(invalid_data):
    with pytest.raises(ValueError):
        _tokenize_line(
            invalid_data,
            filename="fake_filename",
            line_number=-1,
            caster=_auto_cast_stable,
        )


def test_unit_read(inifile):
    load(inifile)


def test_idempotent_io(inifile):
    data0 = load(inifile)
    with tempfile.TemporaryDirectory() as tmpdir:
        save1 = Path(tmpdir) / "save1"
        save2 = Path(tmpdir) / "save2"
        dump(data0, save1)
        data1 = load(save1)
        dump(data1, save2)

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
        (
            "name true 'true'     'steven bacon'  1",
            {"name": [True, "true", "steven bacon", 1]},
        ),
        (
            # see https://github.com/neutrinoceros/inifix/issues/167
            "dogs Idefix.000000",
            {"dogs": "Idefix.000000"},
        ),
    ],
)
def test_string_casting(data, expected):
    mapping = loads(data)
    assert mapping == expected


@pytest.mark.parametrize(
    "data, expected",
    [
        pytest.param(
            '''[Spam]\nEggs "Bacon  Saussage"''',
            {"Spam": {"Eggs": "Bacon  Saussage"}},
            id="simple strings",
        ),
        pytest.param(
            '''numbers 1 '1' 2.2 '2.2' 3.3.3 "3.3.3"''',
            {"numbers": [1, "1", 2.2, "2.2", "3.3.3", "3.3.3"]},
            id="numbers",
        ),
        pytest.param(
            '''vals  1 'bacon' 2.2 "saussage" True no "a b c d"''',
            {"vals": [1, "bacon", 2.2, "saussage", True, False, "a b c d"]},
            id="mixed bag",
        ),
    ],
)
def test_idempotent_string_parsing(data, expected):
    initial_mapping = loads(data)
    assert initial_mapping == expected
    round_str = dumps(initial_mapping)
    round_mapping = loads(round_str)
    assert round_mapping == initial_mapping


@pytest.mark.parametrize("s", ALL_BOOL_STRINGS)
def test_bool_strings(s):
    if s in TRUTHY_STRINGS:
        b = True
    elif s in FALSY_STRINGS:
        b = False
    else:  # pragma: no cover
        raise RuntimeError
    # test unsupported case
    S = s.title().swapcase()
    data = loads(f"a {s} '{s}' {S}")
    assert data == {"a": [b, s, S]}


def test_invalid_section_value():
    val = frozenset((1, 2, 3))
    with pytest.raises(
        TypeError,
        match=re.escape(
            "Expected all values to be scalars or lists of scalars. "
            f"Received invalid values {val}"
        ),
    ):
        _validate_section_item("key", val)


def test_invalid_section_key():
    with pytest.raises(
        TypeError,
        match=re.escape("Expected str keys. Received invalid key: 1"),
    ):
        _validate_section_item(1, True)


@pytest.mark.parametrize("mode", ("w", "wb"))
def test_dump_to_file_descriptor(mode, inifile, tmp_path):
    conf = load(inifile)

    file = tmp_path / "save.ini"
    with open(file, mode=mode) as fh:
        dump(conf, fh)

    # a little weak but better than just testing that the file isn't empty
    new_body = file.read_text()
    for key, val in conf.items():
        if isinstance(val, dict):
            assert f"[{key}]\n" in new_body


def test_dump_to_file_path(inifile, tmp_path):
    conf = load(inifile)

    # pathlib.Path obj
    file1 = tmp_path / "save1.ini"
    dump(conf, file1, skip_validation=True)
    body1 = file1.read_text()

    # str
    file2 = tmp_path / "save2.ini"
    sfile2 = str(file2)
    dump(conf, sfile2, skip_validation=True)
    body2 = file2.read_text()

    assert body1 == body2
    for key, val in conf.items():
        if isinstance(val, dict):
            assert f"[{key}]\n" in body2


def test_load_empty_file(tmp_path):
    target = tmp_path / "empty_file"
    target.touch()
    with pytest.raises(
        ValueError, match=re.escape(f"{str(target)!r} appears to be empty.")
    ):
        load(target)


@pytest.mark.parametrize("mode", ("r", "rb"))
def test_load_from_descriptor(inifile, mode):
    with open(inifile, mode=mode) as fh:
        load(fh)


def test_loads_empty_str():
    ret = loads("")
    assert ret == {}


def test_loads_invalid_str():
    with pytest.raises(ValueError, match="Failed to parse line 1: 'invalid'"):
        loads("invalid")


def test_loads_dumps_roundtrip(inifile):
    with open(inifile) as fh:
        data = fh.read()
    d1 = loads(data)
    s1 = dumps(d1)
    d2 = loads(s1)
    assert d1 == d2


def test_error_read_only_file(tmp_path):
    target = tmp_path / "ini"
    target.touch()
    os.chmod(target, S_IREAD)

    data = {"names": ["bob", "alice"]}

    with pytest.raises(
        PermissionError,
        match=re.escape(f"Cannot write to {target} (permission denied)"),
    ):
        dump(data, target)


def test_read_from_binary_io():
    b = BytesIO(b"var 1 2 a b 'hello world'")
    data = load(b)
    assert data == {"var": [1, 2, "a", "b", "hello world"]}


def test_parse_scalars_as_lists(inifile):
    def _validate(conf):
        for value in conf.values():
            if isinstance(value, dict):
                _validate(value)
            else:
                assert type(value) is list  # noqa: E721

    conf1 = load(inifile, parse_scalars_as_lists=True)
    with open(inifile) as fh:
        conf2 = load(fh, parse_scalars_as_lists=True)

    _validate(conf1)
    _validate(conf2)


def test_skip_validation(monkeypatch, tmp_path):
    import inifix

    def _mp_validate_inifile_schema(d, /, **kwargs):
        raise ValueError("gotcha")

    # cannot monkeypatch inifix.validation.validate_inifile_schema directly ...
    monkeypatch.setattr(
        inifix._io, "validate_inifile_schema", _mp_validate_inifile_schema
    )
    ctx = pytest.raises(ValueError, match="gotcha")

    data = "[Static Grid Output]\ndbl.h5    -1.0  -1"

    with ctx:
        loads(data)

    with open(tmp_path / "data.ini", "w") as fh:
        fh.write(data)

    with ctx:
        load(tmp_path / "data.ini")

    conf1 = loads(data, skip_validation=True)
    conf2 = load(tmp_path / "data.ini", skip_validation=True)
    assert conf1 == conf2


@pytest.mark.parametrize(
    "kwargs",
    [
        pytest.param({}, id="implicitly stable"),
        pytest.param({"integer_casting": "stable"}, id="explicitly stable"),
    ],
)
@given(
    st.lists(
        st.one_of(
            st.integers(),
            st.floats(),
            st.booleans(),
            st.text(
                alphabet=st.characters(
                    codec="utf-8",
                    categories=("Nd", "L"),
                    include_characters=[" "],
                )
            ),
        )
    ).filter(lambda L: len(L) > 0)
)
@example([1, ""])  # regression test for gh-243
def test_roundtrip_stability_generated(kwargs, L):
    if len(L) == 1:
        kwargs.setdefault("parse_scalars_as_lists", True)
    data1 = {"a": L}
    data1_rt = loads(dumps(data1), **kwargs)
    assert_dict_equal(data1_rt, data1)

    data2 = {"Section 1": data1, "Section 2": data1}
    data2_rt = loads(dumps(data2), **kwargs)
    assert_dict_equal(data2_rt, data2)


def test_aggressive_integer_casting():
    input_data = "opt 0 1. 2.0 3e0 4.5"
    data = loads(input_data, integer_casting="aggressive")

    expected = {"opt": [0, 1, 2, 3, 4.5]}
    assert list(data.keys()) == ["opt"]
    for item, expected_item in zip(data["opt"], expected["opt"], strict=True):
        assert item == expected_item
        assert type(item) is type(expected_item)


def test_unknown_integer_casting():
    input_data = "opt 0 1. 2.0 3e0 4.5"
    with pytest.raises(
        ValueError,
        match="Unknown integer_casting value 'unknown_strategy'.",
    ):
        loads(input_data, integer_casting="unknown_strategy")


def test_fargo_compat(datadir):
    conf = load(datadir / "fargo-dummy.ini")
    expected = {
        "x": 1,
        "y": 2,
        "z": 3,
    }
    assert conf == expected


def test_pluto_compat(datadir):
    conf = load(datadir / "pluto-DiskPlanet.ini")
    expected = [
        "Grid",
        "Chombo Refinement",
        "Time",
        "Solver",
        "Boundary",
        "Static Grid Output",
        "Chombo HDF5 output",
        "Parameters",
    ]
    sections = list(conf.keys())
    assert sections == expected


@pytest.mark.skipif(
    sys.version_info < (3, 14),
    reason="annotationlib is new in Python 3.14",
)
@pytest.mark.parametrize("func", [load, loads, dump, dumps])
@pytest.mark.parametrize("format", ["VALUE", "FORWARDREF", "STRING"])
def test_runtime_annotations(func, format):  # pragma: no cover
    from annotationlib import Format, get_annotations

    # check that no exception is raised
    # this test *may* be refined once Python 3.14 is out of beta
    get_annotations(func, format=getattr(Format, format))
    get_annotations(func, eval_str=True)
