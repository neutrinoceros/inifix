import argparse
import os
import re
import sys
from difflib import unified_diff
from io import StringIO
from typing import Generator
from typing import List
from typing import Optional
from typing import Sequence
from typing import TextIO
from typing import Union

from inifix.io import load

PADDING_SIZE = 2


def _normalize_whitespace(s: str) -> str:
    return re.sub(r"\s", " ", s).strip()


def _format_section(data: str) -> str:
    lines = data.splitlines()
    contents = []
    comments = []
    parameters = []
    values = []
    for line in lines:
        content, _, comment = line.partition("#")
        content = _normalize_whitespace(content)
        if not content and not comment:
            continue
        contents.append(content)
        comments.append(_normalize_whitespace(comment))
        if content.startswith("[") or not content:
            continue
        parameter, *value = content.split()
        parameters.append(parameter)
        values.append(value)

    column_sizes: List[int] = []
    if not parameters:
        max_name_size = 0
    else:
        max_name_size = max(len(parameter) for parameter in parameters)
        num_value_cols = max(len(_) for _ in values)

        while len(column_sizes) < num_value_cols:
            new_column_idx = len(column_sizes)
            size = 0
            for v in values:
                if len(v) < new_column_idx + 1:
                    continue
                size = max(size, len(v[new_column_idx]))
            column_sizes.append(size + PADDING_SIZE)

    padded_name_col_size = max_name_size + 2 * PADDING_SIZE
    content_size = padded_name_col_size + sum(column_sizes) + PADDING_SIZE

    new_lines = []
    parameter_idx = 0
    for content, comment in zip(contents, comments):
        new_line = ""
        offset = 0
        if content:
            if content.startswith("["):
                new_line += f"{content}\n"
            else:
                new_line += parameters[parameter_idx].ljust(padded_name_col_size)
                for val, size in zip(values[parameter_idx], column_sizes):
                    new_line += val.ljust(size)
                parameter_idx += 1
                new_line = new_line.strip()
                offset = content_size - len(new_line)
        if comment:
            comm = f"# {comment}"
            new_line += comm.rjust(offset + len(comm))
        new_lines.append(new_line)
    res = "\n".join(new_lines)

    return res


def _finalize(res: str) -> str:
    # compress any duplicate new lines
    res = re.sub("\n+", "\n", res)
    # add one empty line before a new section
    res = re.sub(r"(.?)\n\[", r"\1\n\n[", res)
    # ensure there's exactly one newline at the EOF
    res = res.rstrip("\n")
    res += "\n"
    return res


def _iter_sections(fh: Union[StringIO, TextIO]) -> Generator[str, None, None]:
    line = fh.readline()
    while line != "":
        content = [line]
        while (line := fh.readline()) != "" and not line.startswith("["):
            content.append(line)
        yield "".join(content)


def iniformat(fh: Union[StringIO, TextIO, str], /) -> str:
    if isinstance(fh, str):
        fh = StringIO(fh)
    content = []
    for s in _iter_sections(fh):
        content.append(_format_section(s))
    return _finalize("\n".join(content))


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+")
    parser.add_argument(
        "--diff",
        action="store_true",
        help="Print the unified diff to stdout instead of editing files inplace",
    )

    args = parser.parse_args(argv)

    retv = 0

    for file in args.files:
        if not os.path.isfile(file):
            print(f"Error: could not find {file}", file=sys.stderr)
            retv = 1
            continue
        try:
            load(file)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            retv = 1
            continue

        with open(file) as fh:
            data = fh.read()

        fmted_data = iniformat(data)

        if fmted_data == data:
            print(f"{file} is already formatted", file=sys.stderr)
            continue
        else:
            retv = 1

        if args.diff:
            for line in unified_diff(
                data.splitlines(), fmted_data.splitlines(), fromfile=file
            ):
                if sys.version_info >= (3, 9):
                    line = line.removesuffix("\n")
                elif line.endswith("\n"):
                    line = line[:-1]
                print(line)
            print("\n")
        else:
            print(f"Fixing {file}", file=sys.stderr)
            try:
                with open(file, "w") as fh:
                    fh.write(fmted_data)
            except OSError:
                print(f"Error: could not write to {file}", file=sys.stderr)
                retv = 1
                continue

    return retv


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
