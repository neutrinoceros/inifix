import re

from more_itertools import always_iterable

from inifix.enotation import ENotationIO
from inifix.validation import validate_inifile_schema

SECTION_REGEXP = re.compile(r"\[.+\]\s*")


class IdefixConf(dict):
    def __init__(self, dict_or_path_or_buffer):
        """
        Parse a .ini idefix configuration from a file, or a dict.

        Parameters
        ----------
        dict_filepath_or_buffer: dict, os.Pathlike or str or a readable file handle.
        """
        if isinstance(dict_or_path_or_buffer, dict):
            validate_inifile_schema(dict_or_path_or_buffer)
            super(IdefixConf, self).__init__(dict_or_path_or_buffer)
            return
        self.from_file(dict_or_path_or_buffer)

    def from_file(self, filepath_or_buffer):
        _dict = {}
        try:
            data = filepath_or_buffer.read()
        except AttributeError:
            # this is a path
            with open(filepath_or_buffer, mode="rt") as fh:
                data = fh.read()
        lines = IdefixConf.normalize_data(data)

        for line in lines:
            section = re.match(SECTION_REGEXP, line)
            if section is not None:
                current_section = section.group().strip("[]")
                _dict[current_section] = {}
                continue

            key, values = IdefixConf.tokenize_line(line)
            if len(values) == 1:
                values = values[0]
            _dict[current_section][key] = values
        super(IdefixConf, self).__init__(_dict)

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

    def write_to_buffer(self, buffer):
        is_first = True
        for section, data in self.items():
            if not is_first:
                buffer.write("\n\n")
            lines = []
            buffer.write("[{}]\n\n".format(section))
            for key, val in data.items():
                line = "{}  ".format(key)
                str_val = []
                for v in always_iterable(val):
                    if isinstance(v, (float, int)):
                        str_v = ENotationIO.encode_preferential(v)
                    else:
                        str_v = str(v)
                    str_val.append(str_v)
                val = "  ".join([v for v in str_val])
                line += str(val)
                lines.append(line)

            buffer.write("\n".join(lines) + "\n")
            is_first = False

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
