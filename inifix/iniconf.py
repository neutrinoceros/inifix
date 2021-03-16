import re
from collections import defaultdict
from io import TextIOWrapper

from more_itertools import always_iterable, mark_ends

from inifix._typing import IterableOrSingle, Scalar
from inifix.enotation import ENotationIO
from inifix.validation import validate_inifile_schema

SECTION_REGEXP = re.compile(r"\[.+\]\s*")


class IniConf(dict):
    def __init__(self, dict_or_path_or_buffer):
        """
        Parse a .ini configuration from a file, or a dict.

        Parameters
        ----------
        dict_filepath_or_buffer: dict, os.Pathlike or str or a readable file handle.
        """
        if isinstance(dict_or_path_or_buffer, dict):
            validate_inifile_schema(dict_or_path_or_buffer)
            super(IniConf, self).__init__(dict_or_path_or_buffer)
            return
        self.from_file(dict_or_path_or_buffer)

    def from_file(self, filepath_or_buffer):
        _dict = defaultdict(dict)

        try:
            data = filepath_or_buffer.read()
        except AttributeError:
            # this is a path
            with open(filepath_or_buffer, mode="rt") as fh:
                data = fh.read()
        lines = IniConf.normalize_data(data)

        target = _dict
        for line in lines:
            if (match := re.match(SECTION_REGEXP, line)) is not None:
                target = _dict[match.group().strip("[]")]
                continue

            key, values = IniConf.tokenize_line(line)
            if len(values) == 1:
                values = values[0]
            target[key] = values
        super(IniConf, self).__init__(_dict)

    @staticmethod
    def normalize_data(data):
        # normalize text body `data` to parsable text lines
        lines = []
        for line in data.split("\n"):
            if "#" in line:
                # remove comments
                line = line[: line.index("#")]

            # normalize whitespace
            line = line.strip()
            line = re.sub(r"\s", " ", line)
            if line != "":
                lines.append(line)
        return lines

    @staticmethod
    def tokenize_line(line):
        key, *raw_values = line.split()
        if not raw_values:
            raise ValueError("Could not parse invalid line\n{}".format(line))

        values = []
        for val in raw_values:
            # remove period and trailing zeros to cast to int when possible
            val = re.sub(r"\.0+$", "", val)
            for caster in [int, ENotationIO.decode, float, str]:
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
    def _write_line(
        key: str, values: IterableOrSingle[Scalar], buffer: TextIOWrapper
    ) -> None:
        val_repr = [IniConf.encode(v) for v in always_iterable(values)]
        buffer.write(f"{key} {'  '.join([v for v in val_repr])}\n")

    def write_to_buffer(self, buffer):
        for _is_first, is_last, (key, val) in mark_ends(self.items()):
            if not isinstance(val, dict):
                self._write_line(key, val, buffer)
                continue
            buffer.write("[{}]\n".format(key))
            for k, v in val.items():
                self._write_line(k, v, buffer)
            if not is_last:
                buffer.write("\n")

    def write_to_file(self, filepath):
        with open(filepath, mode="wt") as fh:
            self.write_to_buffer(fh)

    def write(self, filepath_or_buffer):
        """
        Dump a dict to file in idefix's .ini format.
        """
        try:
            self.write_to_buffer(filepath_or_buffer)
        except AttributeError:
            self.write_to_file(filepath_or_buffer)
