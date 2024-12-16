from __future__ import annotations

import os
import re
from collections.abc import Callable, Mapping
from functools import partial
from io import BufferedIOBase, IOBase
from typing import TYPE_CHECKING, Any, Literal, cast, overload

from inifix._more import always_iterable
from inifix._typing import (
    AnyConfig,
    Config_SectionsForbidden_ScalarsAllowed,
    Config_SectionsForbidden_ScalarsForbidden,
    Config_SectionsRequired_ScalarsAllowed,
    Config_SectionsRequired_ScalarsForbidden,
    Scalar,
    StrLike,
)
from inifix.enotation import ENotationIO
from inifix.validation import SCALAR_TYPES, validate_inifile_schema

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Iterable

    from _typeshed import GenericPath

    from inifix._typing import Config_SectionsAllowed_ScalarsForbidden

__all__ = [
    "dump",
    "dumps",
    "load",
    "loads",
]

SECTION_REGEXP = re.compile(r"\[(?P<title>[^(){}\[\]]+)\]\s*")


def _is_numeric(s: str) -> bool:
    try:
        float(s)
    except ValueError:
        return False
    else:
        return True


class Section(dict[str, Any]):
    def __init__(
        self,
        data: Mapping[str, Iterable[Scalar] | Scalar] | None = None,
        /,
        *,
        name: str | None = None,
    ) -> None:
        super().__init__()
        if data is not None:
            for k, v in data.items():
                self[k] = v
        self.name = name

    def __setitem__(self, k: Any, v: Any) -> None:
        if not isinstance(k, str):
            raise TypeError(f"Expected str keys. Received invalid key: {k}")

        if not (
            isinstance(v, SCALAR_TYPES)
            or (isinstance(v, list) and all(isinstance(_, SCALAR_TYPES) for _ in v))
        ):
            raise TypeError(
                "Expected all values to be scalars or lists of scalars. "
                f"Received invalid values {v}"
            )

        super().__setitem__(k, v)

    def _dump_to(self, storage: AnyConfig) -> None:
        if self.name is None:
            storage = cast(
                Config_SectionsForbidden_ScalarsAllowed
                | Config_SectionsForbidden_ScalarsForbidden,
                storage,
            )
            storage.update(self)
        else:
            storage = cast(
                Config_SectionsRequired_ScalarsAllowed
                | Config_SectionsRequired_ScalarsAllowed,
                storage,
            )
            storage[self.name] = dict(self)


# load helper functions


# this is more efficient than running str.partition in a loop
_SPLIT_COMMENTS = partial(str.split, sep="#", maxsplit=1)


def _normalize_data(data: StrLike) -> list[str]:
    # normalize text body `data` to parsable text lines
    if isinstance(data, bytes):
        data = data.decode("utf-8")
    return [line.strip() for (line, *_) in map(_SPLIT_COMMENTS, data.splitlines())]


_TOKEN = re.compile(r"""'[^']*'|"[^"]*"|\S+""")


def _split_tokens(data: str) -> list[str]:
    return _TOKEN.findall(data)


TRUTHY_STRINGS = frozenset({"true", "TRUE", "True", "yes", "YES", "Yes"})
FALSY_STRINGS = frozenset({"false", "FALSE", "False", "no", "NO", "No"})
ALL_BOOL_STRINGS = frozenset({*TRUTHY_STRINGS, *FALSY_STRINGS})

_RE_CASTERS: list[tuple[re.Pattern, Callable[[str], Any]]] = [
    (re.compile("(" + "|".join(TRUTHY_STRINGS) + ")"), lambda _: True),
    (re.compile("(" + "|".join(FALSY_STRINGS) + ")"), lambda _: False),
    (re.compile(r"^'.*'$"), lambda s: s[1:-1]),
    (re.compile(r'^".*"$'), lambda s: s[1:-1]),
]


def _auto_cast_aggressive(s: str) -> Scalar:
    try:
        f = float(s)
    except ValueError:
        pass
    else:
        if f.is_integer():
            return int(f)
        else:
            return f

    for regexp, caster in _RE_CASTERS:
        if regexp.fullmatch(s):
            return caster(s)

    return s


def _auto_cast_stable(s: str) -> Scalar:
    try:
        return int(s)
    except ValueError:
        pass

    try:
        return float(s)
    except ValueError:
        pass

    for regexp, caster in _RE_CASTERS:
        if regexp.fullmatch(s):
            return caster(s)

    return s


CasterFunction = Callable[[str], Scalar]


def _get_caster(integer_casting: Literal["stable", "aggressive"]) -> CasterFunction:
    match integer_casting:
        case "stable":
            return _auto_cast_stable
        case "aggressive":
            return _auto_cast_aggressive
        case _:
            raise ValueError(
                f"Unknown integer_casting value {integer_casting!r}. "
                "Expected 'stable' or 'aggressive'."
            )


def _tokenize_line(
    line: str,
    line_number: int,
    filename: str | None,
    caster: CasterFunction,
) -> tuple[str, list[Scalar]]:
    key, *raw_values = _split_tokens(line)
    if not raw_values:
        if filename is None:
            raise ValueError(f"Failed to parse line {line_number}: {line!r}")
        else:
            raise ValueError(f"Failed to parse {filename}:{line_number}:\n{line}")

    return key, [caster(v) for v in raw_values]


def _from_string(
    data: StrLike,
    *,
    parse_scalars_as_lists: bool,
    caster: CasterFunction,
    filename: str | None = None,
) -> AnyConfig:
    container: AnyConfig = {}
    lines = _normalize_data(data)
    section = Section()  # the default target is a nameless section
    for line_number, line in enumerate(lines, start=1):
        if not line:
            continue
        match = SECTION_REGEXP.fullmatch(line)
        if match is not None:
            if section:
                section._dump_to(container)
            section = Section(name=match["title"])
            continue

        values: Scalar | list[Scalar]
        key, values = _tokenize_line(
            line, filename=filename, line_number=line_number, caster=caster
        )
        if (not parse_scalars_as_lists) and len(values) == 1:
            values = values[0]
        section[key] = values
    section._dump_to(container)
    return container


def _from_file_descriptor(
    file: IOBase,
    *,
    parse_scalars_as_lists: bool,
    caster: CasterFunction,
) -> AnyConfig:
    filename = str(getattr(file, "name", repr(file)))
    data = file.read()
    lines = _normalize_data(data)
    if not "".join(lines):
        raise ValueError(f"{filename!r} appears to be empty.")
    return _from_string(
        data,
        filename=filename,
        parse_scalars_as_lists=parse_scalars_as_lists,
        caster=caster,
    )


def _from_path(
    file: GenericPath[str],
    *,
    parse_scalars_as_lists: bool,
    caster: CasterFunction,
) -> AnyConfig:
    file = os.fspath(file)
    with open(file, "rb") as fh:
        return _from_file_descriptor(
            fh,
            parse_scalars_as_lists=parse_scalars_as_lists,
            caster=caster,
        )


# dump helper functions


def _encode(v: Scalar) -> str:
    if isinstance(v, float):
        return ENotationIO.encode_preferential(v)
    elif isinstance(v, str) and (
        v == ""
        or re.search(r"\s", v) is not None
        or v in ALL_BOOL_STRINGS
        or _is_numeric(v)
    ):
        return repr(v)
    else:
        return str(v)


def _write(content: str, buffer: IOBase) -> None:
    if isinstance(buffer, BufferedIOBase):
        buffer.write(content.encode("utf-8"))
    else:
        buffer.write(content)


def _write_line(key: str, values: Iterable[Scalar] | Scalar, buffer: IOBase) -> None:
    val_repr = [_encode(v) for v in always_iterable(values)]
    _write(f"{key} {'  '.join(list(val_repr))}\n", buffer)


def _write_to_buffer(data: AnyConfig, buffer: IOBase) -> None:
    last = len(data) - 1
    for i, (key, val) in enumerate(data.items()):
        if not isinstance(val, dict):
            _write_line(key, val, buffer)
            continue
        _write(f"[{key}]\n", buffer)
        for k, v in val.items():
            _write_line(k, v, buffer)
        if i < last:
            _write("\n", buffer)


def _write_to_file(data: AnyConfig, file: GenericPath[str], /) -> None:
    if os.path.exists(file) and not os.access(file, os.W_OK):
        raise PermissionError(f"Cannot write to {file} (permission denied)")

    from tempfile import TemporaryDirectory

    with TemporaryDirectory(dir=os.path.dirname(file)) as tmpdir:
        tmpfile = os.path.join(tmpdir, "ini")
        with open(tmpfile, "wb") as fh:
            _write_to_buffer(data, fh)
        os.replace(tmpfile, file)


# narrowing return type on *two* keyword arguments at once:
# sections and parse_scalars_as_list

# these overloads are tricky to get right:
# - to avoid signature overlaps, we need to indicate default values in overloads
#   as often as possible
# - default values can only be specified where they match the annotated type
# - all arguments with default values need to come last in the signature
# - only keyword-only arguments can be re-arranged
# - since I'm overloading over two arguments at the same time, the above
#   *implies* that I can only do it for keyword-only arguments

# overloads are sorted from most to lease strict return type


@overload
def load(
    source: GenericPath[str] | IOBase,
    /,
    *,
    sections: Literal["forbid"],
    parse_scalars_as_lists: Literal[True],
    integer_casting: Literal["stable", "aggressive"] = "stable",
    skip_validation: bool = False,
) -> Config_SectionsForbidden_ScalarsForbidden: ...
@overload
def load(
    source: GenericPath[str] | IOBase,
    /,
    *,
    sections: Literal["require"],
    parse_scalars_as_lists: Literal[True],
    integer_casting: Literal["stable", "aggressive"] = "stable",
    skip_validation: bool = False,
) -> Config_SectionsRequired_ScalarsForbidden: ...
@overload
def load(
    source: GenericPath[str] | IOBase,
    /,
    *,
    sections: Literal["forbid"],
    parse_scalars_as_lists: Literal[False] = False,
    integer_casting: Literal["stable", "aggressive"] = "stable",
    skip_validation: bool = False,
) -> Config_SectionsForbidden_ScalarsAllowed: ...
@overload
def load(
    source: GenericPath[str] | IOBase,
    /,
    *,
    sections: Literal["require"],
    parse_scalars_as_lists: Literal[False] = False,
    integer_casting: Literal["stable", "aggressive"] = "stable",
    skip_validation: bool = False,
) -> Config_SectionsRequired_ScalarsAllowed: ...
@overload
def load(
    source: GenericPath[str] | IOBase,
    /,
    *,
    parse_scalars_as_lists: Literal[True],
    sections: Literal["allow"] = "allow",
    integer_casting: Literal["stable", "aggressive"] = "stable",
    skip_validation: bool = False,
) -> Config_SectionsAllowed_ScalarsForbidden: ...
@overload
def load(
    source: GenericPath[str] | IOBase,
    /,
    *,
    parse_scalars_as_lists: Literal[False] = False,
    sections: Literal["allow"] = "allow",
    integer_casting: Literal["stable", "aggressive"] = "stable",
    skip_validation: bool = False,
) -> AnyConfig: ...


def load(
    source: GenericPath[str] | IOBase,
    /,
    *,
    # parsing options
    parse_scalars_as_lists: bool = False,
    integer_casting: Literal["stable", "aggressive"] = "stable",
    # validation options
    sections: Literal["allow", "forbid", "require"] = "allow",
    skip_validation: bool = False,
) -> AnyConfig:
    """
    Parse data from a file.

    Parameters
    ----------
    source: any of the following
        - the name of a file to read from, (str, bytes or os.PathLike)
        - a readable handle. Both text and binary file modes are supported,
          though binary is preferred.
          In binary mode, we assume UTF-8 encoding.

    parse_scalars_as_lists: bool (default: False)
        if set to True, all values will be parses as lists of scalars,
        even for parameters comprised of a single scalar.
        This also has the effect of narrowing down the return type as seen
        by static type checkers.

        .. versionadded: 3.1.0

    integer_casting: 'stable' (default) or 'aggressive'
        casting strategy for numbers written in decimal notations, such as '1.',
        '2.0' or '3e0'. By default, perform roundtrip-stable casting (i.e., cast
        as Python floats). Setting `integer_casting='aggressive'` will instead
        parse these as Python ints, matching the behavior of inifix 4.5

        .. versionadded: 5.0.0

    sections: 'allow' (default), 'forbid' or 'require'
        use sections='forbid' to invalidate any section found,
        or sections='require' to invalidate a sectionless structure.
        Default mode (sections='allow') permits both.
        sections='forbid' and sections='require' both have the effect of
        narrowing down the return type as seen by static type checkers.
        This parameter has no effect at runtime when combined with
        skip_validation=True.

        .. versionadded: 5.1.0

    skip_validation: bool (default: False)
        if set to True, input is not validated. This can be used to speedup
        io operations trusted input or to work around bugs with the validation
        routine. Use with caution.
        This parameter intentionally has no effect on static type checking.

        .. versionadded: 4.1.0

    See Also
    --------
    inifix.loads
    """
    caster = _get_caster(integer_casting)

    if isinstance(source, IOBase):
        config = _from_file_descriptor(
            source,
            parse_scalars_as_lists=parse_scalars_as_lists,
            caster=caster,
        )
    else:
        assert isinstance(source, str | bytes | os.PathLike)
        config = _from_path(
            source,
            parse_scalars_as_lists=parse_scalars_as_lists,
            caster=caster,
        )

    if not skip_validation:
        validate_inifile_schema(config, sections=sections)
    return config


@overload
def loads(
    source: str,
    /,
    *,
    sections: Literal["forbid"],
    parse_scalars_as_lists: Literal[True],
    integer_casting: Literal["stable", "aggressive"] = "stable",
    skip_validation: bool = False,
) -> Config_SectionsForbidden_ScalarsForbidden: ...
@overload
def loads(
    source: str,
    /,
    *,
    sections: Literal["require"],
    parse_scalars_as_lists: Literal[True],
    integer_casting: Literal["stable", "aggressive"] = "stable",
    skip_validation: bool = False,
) -> Config_SectionsRequired_ScalarsForbidden: ...
@overload
def loads(
    source: str,
    /,
    *,
    sections: Literal["forbid"],
    parse_scalars_as_lists: Literal[False] = False,
    integer_casting: Literal["stable", "aggressive"] = "stable",
    skip_validation: bool = False,
) -> Config_SectionsForbidden_ScalarsAllowed: ...
@overload
def loads(
    source: str,
    /,
    *,
    sections: Literal["require"],
    parse_scalars_as_lists: Literal[False] = False,
    integer_casting: Literal["stable", "aggressive"] = "stable",
    skip_validation: bool = False,
) -> Config_SectionsRequired_ScalarsAllowed: ...
@overload
def loads(
    source: str,
    /,
    *,
    parse_scalars_as_lists: Literal[True],
    sections: Literal["allow"] = "allow",
    integer_casting: Literal["stable", "aggressive"] = "stable",
    skip_validation: bool = False,
) -> Config_SectionsAllowed_ScalarsForbidden: ...
@overload
def loads(
    source: str,
    /,
    *,
    parse_scalars_as_lists: Literal[False] = False,
    sections: Literal["allow"] = "allow",
    integer_casting: Literal["stable", "aggressive"] = "stable",
    skip_validation: bool = False,
) -> AnyConfig: ...


def loads(
    source: str,
    /,
    *,
    # parsing options
    parse_scalars_as_lists: bool = False,
    integer_casting: Literal["stable", "aggressive"] = "stable",
    # validation options
    sections: Literal["allow", "forbid", "require"] = "allow",
    skip_validation: bool = False,
) -> AnyConfig:
    """
    Parse data from a string.

    Parameters
    ----------
    source: str
        The content of a parameter file (has to be inifix format-compliant)

    parse_scalars_as_lists: bool (default: False)
        if set to True, all values will be parses as lists of scalars,
        even for parameters comprised of a single scalar.
        This also has the effect of narrowing down the return type as seen
        by static type checkers.

        .. versionadded: 3.1.0

    integer_casting: 'stable' (default) or 'aggressive'
        casting strategy for numbers written in decimal notations, such as '1.',
        '2.0' or '3e0'. By default, perform roundtrip-stable casting (i.e., cast
        as Python floats). Setting `integer_casting='aggressive'` will instead
        parse these as Python ints, matching the behavior of inifix 4.5

        .. versionadded: 5.0.0

    sections: 'allow' (default), 'forbid' or 'require'
        use sections='forbid' to invalidate any section found,
        or sections='require' to invalidate a sectionless structure.
        Default mode (sections='allow') permits both.
        sections='forbid' and sections='require' both have the effect of
        narrowing down the return type as seen by static type checkers.
        This parameter has no effect at runtime when combined with
        skip_validation=True.

        .. versionadded: 5.1.0

    skip_validation: bool (default: False)
        if set to True, input is not validated. This can be used to speedup
        io operations trusted input or to work around bugs with the validation
        routine. Use with caution.
        This parameter intentionally has no effect on static type checking.

        .. versionadded: 4.1.0

    See Also
    --------
    inifix.load
    """
    caster = _get_caster(integer_casting)
    retv = _from_string(
        source, parse_scalars_as_lists=parse_scalars_as_lists, caster=caster
    )

    if not skip_validation:
        validate_inifile_schema(retv, sections=sections)
    return retv


def dump(
    data: AnyConfig,
    /,
    file: GenericPath[str] | IOBase,
    *,
    # validation options
    sections: Literal["allow", "forbid", "require"] = "allow",
    skip_validation: bool = False,
) -> None:
    """
    Write data to a file.

    Parameters
    ----------
    data: dict
        has to be inifix format-compliant

    file: any of the following
        - the name of a file to write to (str, bytes or os.PathLike)
        - a writable handle. Both text and binary file modes are supported,
          though binary is preferred.
          In binary mode, data is encoded as UTF-8.

    sections: 'allow' (default), 'forbid' or 'require'
        use sections='forbid' to invalidate any section found,
        or sections='require' to invalidate a sectionless structure.
        Default mode (sections='allow') permits both.
        sections='forbid' and sections='require' both have the effect of
        narrowing down the return type as seen by static type checkers.
        This parameter has no effect at runtime when combined with
        skip_validation=True.

        .. versionadded: 5.1.0

    skip_validation: bool (default: False)
        if set to True, input is not validated. This can be used to speedup
        io operations trusted input or to work around bugs with the validation
        routine. Use with caution.
        This parameter intentionally has no effect on static type checking.

        .. versionadded: 4.1.0

    See Also
    --------
    inifix.dumps
    """
    if not skip_validation:
        validate_inifile_schema(data, sections=sections)

    if isinstance(file, IOBase):
        _write_to_buffer(data, file)
    else:
        _write_to_file(data, file)


def dumps(
    data: AnyConfig,
    /,
    *,
    # validation options
    sections: Literal["allow", "forbid", "require"] = "allow",
    skip_validation: bool = False,
) -> str:
    """
    Convert data to a string.

    Parameters
    ----------
    data: dict
        has to be inifix format-compliant

    sections: 'allow' (default), 'forbid' or 'require'
        use sections='forbid' to invalidate any section found,
        or sections='require' to invalidate a sectionless structure.
        Default mode (sections='allow') permits both.
        sections='forbid' and sections='require' both have the effect of
        narrowing down the return type as seen by static type checkers.
        This parameter has no effect at runtime when combined with
        skip_validation=True.

        .. versionadded: 5.1.0

    skip_validation: bool (default: False)
        if set to True, input is not validated. This can be used to speedup
        io operations trusted input or to work around bugs with the validation
        routine. Use with caution.
        This parameter intentionally has no effect on static type checking.

        .. versionadded: 4.1.0

    Returns
    -------
    string representing the content of a parameter file

    See Also
    --------
    inifix.dump
    """
    from io import BytesIO

    s = BytesIO()
    dump(data, file=s, skip_validation=skip_validation, sections=sections)
    return s.getvalue().decode("utf-8")
