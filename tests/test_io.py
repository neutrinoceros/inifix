import difflib
import os
import re
import sys
import tempfile
from collections.abc import Sequence
from io import BytesIO
from pathlib import Path
from stat import S_IREAD
from typing import Any, Literal, NotRequired, TypedDict

import pytest
from hypothesis import example, given
from hypothesis import strategies as st

from inifix import dump, dumps, load, loads
from inifix._io import (
    ALL_BOOL_STRINGS,
    FALSY_STRINGS,
    TRUTHY_STRINGS,
    auto_cast_stable,
    tokenize_line,
    validate_section_item,
)
from inifix._testing import assert_mapping_equal
from inifix._typing import AnyConfig, Scalar

if sys.version_info >= (3, 14):
    from annotationlib import Format, get_annotations
else:
    from typing_extensions import Format, get_annotations


@pytest.mark.parametrize(
    "invalid_data", ["", "SingleToken", "[InvalidSectionName", "InvalidSection]"]
)
def test_tokenizer(invalid_data: str) -> None:
    with pytest.raises(ValueError):
        tokenize_line(
            invalid_data,
            filename="fake_filename",
            line_number=-1,
            caster=auto_cast_stable,
        )


def test_unit_read(inifile: Path) -> None:
    load(inifile)


def test_idempotent_io(inifile: Path) -> None:
    data0 = load(inifile)
    with tempfile.TemporaryDirectory() as tmpdir:
        save1 = Path(tmpdir) / "save1"
        save2 = Path(tmpdir) / "save2"
        dump(data0, save1)
        data1 = load(save1)
        dump(data1, save2)

        text1 = save1.read_text(encoding="utf-8").split("\n")
        text2 = save2.read_text(encoding="utf-8").split("\n")

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
def test_string_casting(data: str, expected: AnyConfig) -> None:
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
def test_idempotent_string_parsing(data: str, expected: AnyConfig) -> None:
    initial_mapping = loads(data)
    assert initial_mapping == expected
    round_str = dumps(initial_mapping)
    round_mapping = loads(round_str)
    assert round_mapping == initial_mapping


@pytest.mark.parametrize("s", ALL_BOOL_STRINGS)
def test_bool_strings(s: str) -> None:
    if s in TRUTHY_STRINGS:
        b = True
    elif s in FALSY_STRINGS:
        b = False
    else:
        raise RuntimeError
    # test unsupported case
    S = s.title().swapcase()
    data = loads(f"a {s} '{s}' {S}")
    assert data == {"a": [b, s, S]}


def test_invalid_section_value() -> None:
    val = frozenset((1, 2, 3))
    with pytest.raises(
        TypeError,
        match=re.escape(
            "Expected all values to be scalars or lists of scalars. "
            f"Received invalid values {val}"
        ),
    ):
        validate_section_item("key", val)  # type: ignore


def test_invalid_section_key() -> None:
    with pytest.raises(
        TypeError,
        match=re.escape("Expected str keys. Received invalid key: 1"),
    ):
        validate_section_item(
            1,  # type: ignore
            True,
        )


class OpenKwargs(TypedDict):
    mode: NotRequired[Literal["w", "wb"]]
    encoding: NotRequired[str]


@pytest.mark.parametrize(
    "open_kwargs",
    [
        pytest.param({"mode": "w", "encoding": "utf-8"}, id="text write"),
        pytest.param({"mode": "wb"}, id="bin write"),
    ],
)
def test_dump_to_file_descriptor(
    inifile: Path, open_kwargs: OpenKwargs, tmp_path: Path
) -> None:
    conf = load(inifile)

    file = tmp_path / "save.ini"
    with open(file, **open_kwargs) as fh:
        dump(conf, fh)

    # a little weak but better than just testing that the file isn't empty
    new_body = file.read_text(encoding="utf-8")
    for key, val in conf.items():
        if isinstance(val, dict):
            assert f"[{key}]\n" in new_body

    assert_mapping_equal(loads(new_body), conf)


def test_dump_to_file_path(inifile: Path, tmp_path: Path) -> None:
    conf = load(inifile)

    # pathlib.Path obj
    file1 = tmp_path / "save1.ini"
    dump(conf, file1, skip_validation=True)
    body1 = file1.read_text(encoding="utf-8")

    # str
    file2 = tmp_path / "save2.ini"
    sfile2 = str(file2)
    dump(conf, sfile2, skip_validation=True)
    body2 = file2.read_text(encoding="utf-8")

    assert body1 == body2
    for key, val in conf.items():
        if isinstance(val, dict):
            assert f"[{key}]\n" in body2

    assert_mapping_equal(loads(body1), conf)
    assert_mapping_equal(loads(body2), conf)


def test_load_empty_file(tmp_path: Path) -> None:
    target = tmp_path / "empty_file"
    target.touch()
    with pytest.raises(
        ValueError, match=re.escape(f"{str(target)!r} appears to be empty.")
    ):
        load(target)


@pytest.mark.parametrize(
    "open_kwargs",
    [
        pytest.param({"encoding": "utf-8"}, id="text read"),
        pytest.param({"mode": "rb"}, id="bin read"),
    ],
)
def test_load_from_descriptor(inifile: Path, open_kwargs: OpenKwargs) -> None:
    with open(inifile, **open_kwargs) as fh:
        load(fh)


def test_loads_empty_str() -> None:
    ret = loads("")
    assert ret == {}


def test_loads_invalid_str() -> None:
    with pytest.raises(ValueError, match="Failed to parse line 1: 'invalid'"):
        loads("invalid")


def test_loads_dumps_roundtrip(inifile: Path) -> None:
    with open(inifile, encoding="utf-8") as fh:
        data = fh.read()
    d1 = loads(data)
    s1 = dumps(d1)
    d2 = loads(s1)
    assert_mapping_equal(d2, d2)


def test_error_read_only_file(tmp_path: Path) -> None:
    target = tmp_path / "ini"
    target.touch()
    os.chmod(target, S_IREAD)

    data = {"names": ["bob", "alice"]}

    with pytest.raises(
        PermissionError,
        match=re.escape(f"Cannot write to {target} (permission denied)"),
    ):
        dump(data, target)


def test_read_from_binary_io() -> None:
    b = BytesIO(b"var 1 2 a b 'hello world'")
    data = load(b)
    assert data == {"var": [1, 2, "a", "b", "hello world"]}


def test_parse_scalars_as_lists(inifile: Path) -> None:
    def _validate(conf: AnyConfig) -> None:
        for value in conf.values():
            if isinstance(value, dict):
                _validate(value)
            else:
                assert type(value) is list  # noqa: E721

    conf1 = load(inifile, parse_scalars_as_lists=True)
    with open(inifile, encoding="utf-8") as fh:
        conf2 = load(fh, parse_scalars_as_lists=True)

    _validate(conf1)
    _validate(conf2)


def test_skip_validation(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import inifix

    def _mp_validate_inifile_schema(_d: AnyConfig, /, **_kwargs: object) -> None:
        raise ValueError("gotcha")

    # cannot monkeypatch inifix.validation.validate_inifile_schema directly ...
    monkeypatch.setattr(
        inifix._io,  # pyright: ignore[reportPrivateUsage]
        "validate_inifile_schema",
        _mp_validate_inifile_schema,
    )
    ctx = pytest.raises(ValueError, match="gotcha")

    data = "[Static Grid Output]\ndbl.h5    -1.0  -1"

    with ctx:
        loads(data)

    with open(tmp_path / "data.ini", "w", encoding="utf-8") as fh:
        fh.write(data)

    with ctx:
        load(tmp_path / "data.ini")

    conf1 = loads(data, skip_validation=True)
    conf2 = load(tmp_path / "data.ini", skip_validation=True)
    assert_mapping_equal(conf2, conf1)


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
def test_roundtrip_stability_generated(
    kwargs: dict[str, Any], L: Sequence[Scalar]
) -> None:
    if len(L) == 1:
        kwargs.setdefault("parse_scalars_as_lists", True)
    data1 = {"a": L}
    data1_rt = loads(dumps(data1), **kwargs)
    assert_mapping_equal(data1_rt, data1)

    data2 = {"Section 1": data1, "Section 2": data1}
    data2_rt = loads(dumps(data2), **kwargs)
    assert_mapping_equal(data2_rt, data2)


def test_aggressive_integer_casting() -> None:
    input_data = "opt 0 1. 2.0 3e0 4.5"
    data = loads(input_data, integer_casting="aggressive", parse_scalars_as_lists=True)

    expected = {"opt": [0, 1, 2, 3, 4.5]}
    assert list(data.keys()) == ["opt"]
    for item, expected_item in zip(data["opt"], expected["opt"], strict=True):
        assert item == expected_item
        assert type(item) is type(expected_item)


def test_unknown_integer_casting() -> None:
    input_data = "opt 0 1. 2.0 3e0 4.5"
    with pytest.raises(
        ValueError,
        match="Unknown integer_casting value 'unknown_strategy'.",
    ):
        loads(
            input_data,
            integer_casting="unknown_strategy",  # type: ignore
        )


def test_fargo_compat(datadir: Path) -> None:
    conf = load(datadir / "fargo-dummy.ini")
    expected = {
        "x": 1,
        "y": 2,
        "z": 3,
    }
    assert_mapping_equal(conf, expected)


def test_pluto_compat(datadir: Path) -> None:
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


@pytest.mark.parametrize("func", [load, loads, dump, dumps])
@pytest.mark.parametrize("format", ["VALUE", "FORWARDREF", "STRING"])
def test_runtime_annotations(func: object, format: str) -> None:
    # check that no exception is raised
    get_annotations(func, format=getattr(Format, format))
    get_annotations(func, eval_str=True)
