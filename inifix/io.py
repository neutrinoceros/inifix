import os
import re
from copy import deepcopy
from io import TextIOBase
from typing import Any
from typing import Callable
from typing import cast
from typing import List
from typing import Mapping
from typing import Optional
from typing import TextIO
from typing import Tuple
from typing import Union

from more_itertools import always_iterable
from more_itertools import mark_ends

from inifix._typing import InifixConfT
from inifix._typing import IterableOrSingle
from inifix._typing import PathLike
from inifix._typing import Scalar
from inifix.enotation import ENotationIO
from inifix.validation import SCALAR_TYPES
from inifix.validation import validate_inifile_schema

__all__ = ["load", "dump"]

SECTION_REGEXP = re.compile(r"\[.+\]\s*")


def bool_caster(s: str) -> bool:
    s = s.lower()
    if s in ("true", "t"):
        return True
    elif s in ("false", "f"):
        return False
    raise ValueError


def str_caster(s: str) -> str:
    if re.match(r"^'.*'$", s) or re.match(r'^".*"$', s):
        return s[1:-1]
    else:
        return s


CASTERS: List[Callable] = [
    int,
    float,
    bool_caster,
    str_caster,
]


class Section(dict):
    def __init__(
        self,
        data: Optional[Mapping[str, IterableOrSingle[Scalar]]] = None,
        /,
        *,
        name: Optional[str] = None,
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


def _normalize_data(data: str) -> List[str]:
    # normalize text body `data` to parsable text lines
    lines = []
    for line in data.splitlines():
        # remove comments and normalize whitespace
        line, _, _comment = line.partition("#")
        lines.append(re.sub(r"\s", " ", line.strip()))
    return lines


def _tokenize_line(
    line: str, line_number: int, file: Optional[TextIO]
) -> Tuple[str, List[Scalar]]:
    key, *raw_values = line.split()
    if not raw_values:
        if file is None:
            raise ValueError(f"Failed to parse line {line_number}: {line!r}")
        else:
            raise ValueError(f"Failed to parse {file}:{line_number}:\n{line}")

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


def _from_string(data: str, file: Optional[TextIO] = None) -> InifixConfT:
    # see https://github.com/python/mypy/issues/6463
    container: InifixConfT = {}  # type: ignore[assignment]
    lines = _normalize_data(data)
    section = Section()  # the default target is a nameless section
    for line_number, line in enumerate(lines, start=1):
        if not line:
            continue
        match = re.match(SECTION_REGEXP, line)
        if match is not None:
            if section:
                section._dump_to(container)
            section = Section(name=match.group().strip("[]"))
            continue

        values: Union[Scalar, List[Scalar]]
        key, values = _tokenize_line(line, file=file, line_number=line_number)
        if len(values) == 1:
            values = values[0]
        section[key] = values
    section._dump_to(container)
    return container


def _from_file_descriptor(file: TextIO) -> InifixConfT:
    data = file.read()
    lines = _normalize_data(data)
    if not "".join(lines):
        raise ValueError(f"{file.name!r} appears to be empty.")
    return _from_string(data, file=file)


def _from_path(file: PathLike) -> InifixConfT:
    file = os.fspath(file)
    with open(file) as fh:
        return _from_file_descriptor(fh)


# dump helper functions


def _encode(v: Scalar) -> str:
    if isinstance(v, float):
        return ENotationIO.encode_preferential(v)
    return str(v)


def _write_line(key: str, values: IterableOrSingle[Scalar], buffer: TextIO) -> None:
    val_repr = [_encode(v) for v in always_iterable(values)]
    buffer.write(f"{key} {'  '.join([v for v in val_repr])}\n")


def _write_to_buffer(data: InifixConfT, buffer: TextIO) -> None:
    for _is_first, is_last, (key, val) in mark_ends(data.items()):
        if not isinstance(val, dict):
            _write_line(key, val, buffer)
            continue
        buffer.write(f"[{key}]\n")
        for k, v in val.items():
            _write_line(k, v, buffer)
        if not is_last:
            buffer.write("\n")


def _write_to_file(data: InifixConfT, file: PathLike, /) -> None:
    with open(file, mode="wt") as fh:
        _write_to_buffer(data, fh)


def load(source: Union[InifixConfT, PathLike, TextIO], /) -> InifixConfT:
    """
    Parse data from a file, or a dict.

    Parameters
    ----------
    source: any of the following
        - a dict (has to be inifix format-compliant)
        - the name of a file to read from, (str, bytes or os.PathLike)
        - a readable file handle (assuming text mode)
    """
    if isinstance(source, TextIOBase):
        source = _from_file_descriptor(source)  # type: ignore [arg-type]
    elif isinstance(source, (str, bytes, os.PathLike)):
        source = _from_path(source)

    source = cast(Mapping, source)

    validate_inifile_schema(source)
    source = cast(InifixConfT, source)
    return source


def loads(source: str, /) -> InifixConfT:
    return _from_string(source)


def dump(data: InifixConfT, /, file: Union[PathLike, TextIOBase]) -> None:
    """
    Write data to a file.

    Parameters
    ----------
    data: dict
        has to be inifix format-compliant

    file: any of the following
        - the name of a file to write to (str, bytes or os.PathLike)
        - a writable file handle (assuming text mode)
    """
    validate_inifile_schema(data)

    try:
        _write_to_buffer(data, file)  # type: ignore
    except AttributeError:
        _write_to_file(data, file)


def dumps(data: InifixConfT, /) -> str:
    from io import StringIO

    s = StringIO()
    dump(data, file=s)
    return s.getvalue()
