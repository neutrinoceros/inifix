from __future__ import annotations

import argparse
import os
import re
import sys
from difflib import unified_diff
from io import StringIO
from tempfile import TemporaryDirectory
from typing import IO
from typing import Iterable

from inifix.io import _split_tokens
from inifix.io import load

PADDING_SIZE = 2


def _format_section(data: str) -> str:
    lines = data.splitlines()
    contents = []
    comments = []
    parameters = []
    values = []
    for line in lines:
        content, _, comment = line.partition("#")
        content = content.strip()
        if not content and not comment:
            continue
        contents.append(content)
        comments.append(comment.strip())
        if content.startswith("[") or not content:
            continue
        parameter, *value = _split_tokens(content)
        parameters.append(parameter)
        values.append(value)

    column_sizes: list[int] = []
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


def _iter_sections(fh: IO[str]) -> Iterable[str]:
    line = fh.readline()
    while line != "":
        content = [line]
        while (line := fh.readline()) != "" and not line.startswith("["):
            content.append(line)
        yield "".join(content)


def iniformat(fh: IO[str] | str, /) -> str:
    if isinstance(fh, str):
        fh = StringIO(fh)
    content = []
    for s in _iter_sections(fh):
        content.append(_format_section(s))
    return _finalize("\n".join(content))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+")
    parser.add_argument(
        "--diff",
        action="store_true",
        help="Print the unified diff to stdout instead of editing files inplace",
    )
    parser.add_argument(
        "--report-noop",
        action="store_true",
        help="Explicitly log noops for files that are already formatted",
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

        with open(file, mode="rb") as fh:
            data = fh.read().decode("utf-8")
            # make sure newlines are always decoded as \n, even on windows
            data = data.replace("\r\n", "\n")

        fmted_data = iniformat(data)

        if fmted_data == data:
            if args.report_noop:
                # printing to stderr so that we can pipe into cdiff in --diff mode
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
            if not os.access(file, os.W_OK):
                print(
                    f"Error: could not write to {file} (permission denied)",
                    file=sys.stderr,
                )
                retv = 1
                continue

            with TemporaryDirectory(dir=os.path.dirname(file)) as tmpdir:
                tmpfile = os.path.join(tmpdir, "ini")
                with open(tmpfile, "wb") as bfh:
                    bfh.write(fmted_data.encode("utf-8"))
                # this may still raise an error in the unlikely case of a race condition
                # (if permissions are changed between the look and the leap), but we
                # won't try to catch it unless it happens in production, because it is
                # difficult to test systematically.
                os.replace(tmpfile, file)

    return retv


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
