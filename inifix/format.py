import argparse
import os
import re
import sys
from difflib import unified_diff
from typing import Optional
from typing import Sequence

from inifix.io import load

NAME_COL_MINSIZE = 10
COMMENT_COL = 80
PADDING_SIZE = 4


def _ljust(s: str, width: int) -> str:
    """
    A more flexible str.ljust
    Guarantees the return value has at least one trailing whitespace char,
    even at the cost of going over the specified width.
    """
    justified_name = s.ljust(width)
    if len(s) < width:
        return justified_name
    else:
        return justified_name + " "


def _normalize_whitespace(s: str) -> str:
    return re.sub(r"\s", " ", s).strip()


def iniformat(data: str, *, name_column_size: Optional[int] = None) -> str:
    lines = data.splitlines()
    contents = []
    comments = []
    parameters = []
    values = []
    for line in lines:
        content, _, comment = line.partition("#")
        content = _normalize_whitespace(content)
        contents.append(content)
        comments.append(_normalize_whitespace(comment))
        if not content.startswith("[") and content != "":
            parameter, *value = content.split()
            parameters.append(parameter)
            values.append(value)

    if not parameters:
        max_name_size = 0
    else:
        max_name_size = max(len(parameter) for parameter in parameters)

    if name_column_size is None:
        padded_name_col_size = (
            max(max_name_size + PADDING_SIZE, NAME_COL_MINSIZE) + PADDING_SIZE
        )
    else:
        padded_name_col_size = name_column_size

        if max_name_size >= name_column_size:
            long_parameters = [p for p in parameters if len(p) >= name_column_size]
            print(
                "WARNING: The following names are longer than the "
                f"specified name column size ({name_column_size}).\n"
                + " - "
                + "\n - ".join(long_parameters)
                + "\n"
                + "Additional whitespace will be used.",
                file=sys.stderr,
            )

    new_lines = []
    parameter_idx = 0
    for content, comment in zip(contents, comments):
        new_line = ""
        offset = 0
        if content:
            if content.startswith("["):
                new_line += f"{content}\n"
            else:
                new_line += _ljust(parameters[parameter_idx], padded_name_col_size)
                new_line += "  ".join(values[parameter_idx])

                offset = COMMENT_COL - len(new_line)
                parameter_idx += 1
        comm = f"# {comment}"
        new_line += comm.rjust(offset + len(comm)) if comment else ""
        new_lines.append(new_line)
    res = "\n".join(new_lines)
    res = re.sub("\n+", "\n", res)
    res = re.sub(r"(.?)\n\[", r"\1\n\n\n[", res)
    res = re.sub(r"\]\n+", r"]\n\n", res)
    # ensure there's exactly one newline at the EOF
    res = res.rstrip("\n")
    res += "\n"
    return res


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+")
    parser.add_argument(
        "--diff",
        action="store_true",
        help="Print the unified diff to stdout instead of editing files inplace",
    )
    parser.add_argument(
        "--name-column-size", type=int, help="Fixed length of the parameter column"
    )

    args = parser.parse_args(argv)

    retv = 0

    for file in args.files:
        if not os.path.isfile(file):
            print(f"Error: could not find {file}", file=sys.stderr)
            retv += 1
            continue
        try:
            load(file)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            retv += 1
            continue

        with open(file) as fh:
            data = fh.read()

        fmted_data = iniformat(data, name_column_size=args.name_column_size)

        if fmted_data == data:
            print(f"{file} is already formatted", file=sys.stderr)
            continue
        else:
            retv += 1

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
                retv += 1
                continue

    return retv


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
