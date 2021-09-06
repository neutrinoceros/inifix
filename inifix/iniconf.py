import re
from collections import defaultdict
from functools import singledispatchmethod
from io import TextIOBase
from typing import Callable
from typing import List
from typing import TextIO
from typing import Tuple
from typing import Union

from more_itertools import always_iterable
from more_itertools import mark_ends

from inifix._typing import InifixParsable
from inifix._typing import IterableOrSingle
from inifix._typing import PathLike
from inifix._typing import Scalar
from inifix._typing import Section
from inifix.enotation import ENotationIO
from inifix.validation import validate_inifile_schema

SECTION_REGEXP = re.compile(r"\[.+\]\s*")


def bool_caster(s: str) -> bool:
    s = s.lower()
    if s in ("true", "t"):
        return True
    elif s in ("false", "f"):
        return False
    raise ValueError


class InifixConf(dict):
    @singledispatchmethod
    def __init__(self, input_: PathLike, /) -> None:
        """
        Parse a .ini configuration from a file, or a dict.

        Parameters
        ----------
        input_: dict, os.PathLike or str or a readable file handle.
        """
        with open(input_) as fh:
            self.__init__(fh)

    @__init__.register
    def _(self, input_: dict, /) -> None:
        validate_inifile_schema(input_)
        super().__init__(input_)

    @__init__.register
    def _(self, input_: TextIOBase, /) -> None:
        data = input_.read()

        lines = InifixConf.normalize_data(data)
        if not "".join(lines):
            raise ValueError("input stream appears to be empty.")

        _dict: InifixParsable = defaultdict(dict)
        target: Union[InifixParsable, Section] = _dict
        for line_number, line in enumerate(lines, start=1):
            if not line:
                continue
            if (match := re.match(SECTION_REGEXP, line)) is not None:
                section: Section = _dict[match.group().strip("[]")]
                target = section
                continue

            key, values = InifixConf.tokenize_line(line, line_number=line_number)
            if len(values) == 1:
                values = values[0]
            target[key] = values
        self.__init__(_dict)

    @staticmethod
    def normalize_data(data: str) -> List[str]:
        # normalize text body `data` to parsable text lines
        lines = []
        for line in data.splitlines():
            # remove comments and normalize whitespace
            line, _, _comment = line.partition("#")
            lines.append(re.sub(r"\s", " ", line.strip()))
        return lines

    @staticmethod
    def tokenize_line(line: str, line_number: int) -> Tuple[str, List[Scalar]]:
        key, *raw_values = line.split()
        if not raw_values:
            raise ValueError(f"Failed to parse {line_number}:\n{line}")

        values = []
        for val in raw_values:
            # remove period and trailing zeros to cast to int when possible
            val = re.sub(r"\.0+$", "", val)
            casters: List[Callable] = [int, ENotationIO.decode, float, bool_caster, str]
            for caster in casters:
                # cast to types from stricter to most permissive
                # `str` will always succeed since it is the input type
                try:
                    values.append(caster(val))
                    break
                except ValueError:
                    continue

        return key, values

    @staticmethod
    def encode(v: Scalar) -> str:
        if isinstance(v, (float, int)):
            return ENotationIO.encode_preferential(v)
        return str(v)

    @staticmethod
    def _write_line(key: str, values: IterableOrSingle[Scalar], buffer: TextIO) -> None:
        val_repr = [InifixConf.encode(v) for v in always_iterable(values)]
        buffer.write(f"{key} {'  '.join([v for v in val_repr])}\n")

    def write_to_buffer(self, buffer: TextIO) -> None:
        for _is_first, is_last, (key, val) in mark_ends(self.items()):
            if not isinstance(val, dict):
                self._write_line(key, val, buffer)
                continue
            buffer.write(f"[{key}]\n")
            for k, v in val.items():
                self._write_line(k, v, buffer)
            if not is_last:
                buffer.write("\n")

    def write_to_file(self, filepath: PathLike) -> None:
        with open(filepath, mode="wt") as fh:
            self.write_to_buffer(fh)

    def write(self, filepath_or_buffer: Union[PathLike, TextIO]) -> None:
        """
        Dump a dict to file in idefix's .ini format.
        """
        try:
            self.write_to_buffer(filepath_or_buffer)
        except AttributeError:
            self.write_to_file(filepath_or_buffer)
