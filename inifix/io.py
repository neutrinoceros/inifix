from __future__ import annotations

import os
import re
from copy import deepcopy
from io import BufferedIOBase
from io import IOBase
from typing import Any
from typing import Callable
from typing import cast
from typing import Literal
from typing import Mapping

from more_itertools import always_iterable
from more_itertools import mark_ends

from inifix._typing import InifixConfT
from inifix._typing import IterableOrSingle
from inifix._typing import PathLike
from inifix._typing import Scalar
from inifix._typing import StrLike
from inifix.enotation import ENotationIO
from inifix.validation import SCALAR_TYPES
from inifix.validation import validate_inifile_schema

__all__ = ["load", "loads", "dump", "dumps"]

SECTION_REGEXP = re.compile(r"\[(?P<title>[^(){}\[\]]+)\]\s*")


def bool_caster(s: str) -> bool:
    s = s.lower()
    if s in ("true", "yes"):
        return True
    elif s in ("false", "no"):
        return False
    raise ValueError


def str_caster(s: str) -> str:
    if re.match(r"^'.*'$", s) or re.match(r'^".*"$', s):
        return s[1:-1]
    else:
        return s


def _is_numeric(s: str) -> bool:
    try:
        float(s)
    except ValueError:
        return False
    else:
        return True


CASTERS: list[Callable[[str], Any]] = [
    int,
    float,
    bool_caster,
    str_caster,
]


class Section(dict):
    def __init__(
        self,
        data: Mapping[str, IterableOrSingle[Scalar]] | None = None,
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

        _val = deepcopy(v)  # avoid consuming the original iterable
        if not (
            isinstance(v, SCALAR_TYPES)
            or (
                isinstance(_val, list)
                and all(isinstance(_, SCALAR_TYPES) for _ in _val)
            )
        ):
            raise TypeError(
                "Expected all values to be scalars or lists of scalars. "
                f"Received invalid values {v}"
            )

        super().__setitem__(k, v)

    def _dump_to(self, storage: InifixConfT) -> None:
        if self.name is None:
            storage.update(self)
        else:
            storage[self.name] = dict(self)


# load helper functions


def _normalize_data(data: StrLike) -> list[str]:
    # normalize text body `data` to parsable text lines
    out_lines: list[str] = []
    if isinstance(data, bytes):
        raw_lines = [_.decode("utf-8") for _ in data.splitlines()]
    else:
        raw_lines = data.splitlines()

    for line in raw_lines:
        # remove comments and normalize whitespace
        line, _, _comment = line.partition("#")
        out_lines.append(re.sub(r"\s", " ", line.strip()))
    return out_lines


def _next_token(data: str, pattern: str, start: Literal[0, 1]) -> tuple[str, int]:
    pos: int = start
    while pos < len(data) and not re.match(pattern, data[pos]):
        pos += 1
    if start == 1:
        end = pos + 1
    else:
        end = pos
    token = data[:end]
    return token, pos


def _split_tokens(data: str) -> list[str]:
    tokens = []
    pattern = r"\s"
    start: Literal[0, 1] = 0
    data = data.strip()
    while True:
        token, pos = _next_token(data, pattern, start)
        tokens.append(token)
        data = data[pos + 1 :].strip()
        if not data:
            break
        if data[0] in ('"', "'"):
            pattern = data[0]
            start = 1
        else:
            pattern = r"\s"
            start = 0
    return tokens


def _tokenize_line(
    line: str, line_number: int, filename: str | None
) -> tuple[str, list[Scalar]]:
    key, *raw_values = _split_tokens(line)
    if not raw_values:
        if filename is None:
            raise ValueError(f"Failed to parse line {line_number}: {line!r}")
        else:
            raise ValueError(f"Failed to parse {filename}:{line_number}:\n{line}")

    values = []
    for val in raw_values:
        # remove period and trailing zeros to cast to int when possible
        val = re.sub(r"\.0+$", "", val)

        for caster in CASTERS:
            # cast to types from stricter to most permissive
            # `str` will always succeed since it is the input type
            try:
                values.append(caster(val))
                break
            except ValueError:
                continue

    return key, values


def _from_string(
    data: StrLike, *, parse_scalars_as_lists: bool, filename: str | None = None
) -> InifixConfT:
    # see https://github.com/python/mypy/issues/6463
    container: InifixConfT = {}  # type: ignore[assignment]
    lines = _normalize_data(data)
    section = Section()  # the default target is a nameless section
    for line_number, line in enumerate(lines, start=1):
        if not line:
            continue
        match = re.fullmatch(SECTION_REGEXP, line)
        if match is not None:
            if section:
                section._dump_to(container)
            section = Section(name=match["title"])
            continue

        values: Scalar | list[Scalar]
        key, values = _tokenize_line(line, filename=filename, line_number=line_number)
        if (not parse_scalars_as_lists) and len(values) == 1:
            values = values[0]
        section[key] = values
    section._dump_to(container)
    return container


def _from_file_descriptor(file: IOBase, *, parse_scalars_as_lists: bool) -> InifixConfT:
    filename = str(getattr(file, "name", repr(file)))
    data = file.read()
    lines = _normalize_data(data)
    if not "".join(lines):
        raise ValueError(f"{filename!r} appears to be empty.")
    return _from_string(
        data, filename=filename, parse_scalars_as_lists=parse_scalars_as_lists
    )


def _from_path(file: PathLike, *, parse_scalars_as_lists: bool) -> InifixConfT:
    file = os.fspath(file)
    with open(file, "rb") as fh:
        return _from_file_descriptor(fh, parse_scalars_as_lists=parse_scalars_as_lists)


# dump helper functions


def _encode(v: Scalar) -> str:
    if isinstance(v, float):
        return ENotationIO.encode_preferential(v)
    elif isinstance(v, str) and (
        re.search(r"\s", v) is not None
        or v in ("true", "t", "false", "f")
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


def _write_line(key: str, values: IterableOrSingle[Scalar], buffer: IOBase) -> None:
    val_repr = [_encode(v) for v in always_iterable(values)]
    _write(f"{key} {'  '.join([v for v in val_repr])}\n", buffer)


def _write_to_buffer(data: InifixConfT, buffer: IOBase) -> None:
    for _is_first, is_last, (key, val) in mark_ends(data.items()):
        if not isinstance(val, dict):
            _write_line(key, val, buffer)
            continue
        _write(f"[{key}]\n", buffer)
        for k, v in val.items():
            _write_line(k, v, buffer)
        if not is_last:
            _write("\n", buffer)


def _write_to_file(data: InifixConfT, file: PathLike, /) -> None:
    if os.path.exists(file) and not os.access(file, os.W_OK):
        raise PermissionError(f"Cannot write to {file} (permission denied)")

    from tempfile import TemporaryDirectory

    with TemporaryDirectory(dir=os.path.dirname(file)) as tmpdir:
        tmpfile = os.path.join(tmpdir, "ini")
        with open(tmpfile, "wb") as fh:
            _write_to_buffer(data, fh)
        os.replace(tmpfile, file)


def load(
    source: InifixConfT | PathLike | IOBase, /, *, parse_scalars_as_lists: bool = False
) -> InifixConfT:
    """
    Parse data from a file, or a dict.

    Parameters
    ----------
    source: any of the following
        - a dict (has to be inifix format-compliant)
        - the name of a file to read from, (str, bytes or os.PathLike)
        - a readable handle. Both text and binary file modes are supported,
          though binary is prefered.
          In binary mode, we assume UTF-8 encoding.

    parse_scalars_as_lists: bool
        if set to True, all values will be parses as lists of scalars,
        even for parameters comprised of a single scalar.
    """
    if isinstance(source, IOBase):
        source = _from_file_descriptor(
            source, parse_scalars_as_lists=parse_scalars_as_lists
        )
    elif isinstance(source, (str, bytes, os.PathLike)):
        source = _from_path(source, parse_scalars_as_lists=parse_scalars_as_lists)

    source = cast(Mapping, source)

    validate_inifile_schema(source)
    source = cast(InifixConfT, source)
    return source


def loads(source: str, /, *, parse_scalars_as_lists: bool = False) -> InifixConfT:
    return _from_string(source, parse_scalars_as_lists=parse_scalars_as_lists)


def dump(data: InifixConfT, /, file: PathLike | IOBase) -> None:
    """
    Write data to a file.

    Parameters
    ----------
    data: dict
        has to be inifix format-compliant

    file: any of the following
        - the name of a file to write to (str, bytes or os.PathLike)
        - a writable handle. Both text and binary file modes are supported,
          though binary is prefered.
          In binary mode, data is encoded as UTF-8.
    """
    validate_inifile_schema(data)

    if isinstance(file, IOBase):
        _write_to_buffer(data, file)
    else:
        _write_to_file(data, file)


def dumps(data: InifixConfT, /) -> str:
    from io import BytesIO

    s = BytesIO()
    dump(data, file=s)
    return s.getvalue().decode("utf-8")
