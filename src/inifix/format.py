from __future__ import annotations

import argparse
import os
import re
import sys
import warnings
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor
from difflib import unified_diff
from functools import partial
from io import StringIO
from tempfile import TemporaryDirectory
from typing import IO, Literal

from inifix._cli import Message, TaskResults, get_cpu_count
from inifix.io import _split_tokens, load

__all__ = ["format_string"]

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
    for content, comment in zip(contents, comments, strict=True):
        new_line = ""
        offset = 0
        if content:
            if content.startswith("["):
                new_line += f"{content}\n"
            else:
                new_line += parameters[parameter_idx].ljust(padded_name_col_size)
                for val, size in zip(values[parameter_idx], column_sizes, strict=False):
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


def format_string(s: str, /) -> str:
    """Format a string representing the content of an inifile.

    This only operates on whitespace to and aims to maximize readability.
    Comments are preserved.

    Examples
    --------
    >>> import inifix
    >>> print(inifix.format_string(
    ...     "[Grid]\\n"
    ...     "X1-grid  1    0.0    1024          u    4.0\\n"
    ...     "X2-grid    1    0.0    256 u   1.0 # is ignored in 1D\\n"
    ...     "X3-grid      1    0.0    1       u    1.0  # is ignored in 1D and 2D"
    ... ))
    [Grid]
    X1-grid    1  0.0  1024  u  4.0
    X2-grid    1  0.0  256   u  1.0    # is ignored in 1D
    X3-grid    1  0.0  1     u  1.0    # is ignored in 1D and 2D
    <BLANKLINE>
    """
    fh = StringIO(s)
    content = []
    for s in _iter_sections(fh):
        content.append(_format_section(s))
    return _finalize("\n".join(content))


def iniformat(s: str, /) -> str:
    warnings.warn(
        "inifix.format.iniformat is deprecated since v5.0.0"
        "and will be removed in a future version. "
        "Please use inifix.format_string instead.",
        category=DeprecationWarning,
        stacklevel=2,
    )
    return format_string(s)


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
    parser.add_argument(
        "--skip-validation",
        dest="validate",
        action="store_false",
        help="Skip validation step (formatting unvalidated data may lead to undefined behaviour)",
    )

    args = parser.parse_args(argv)
    closure = partial(
        _format_single_file_cli,
        args_validate=args.validate,
        args_report_noop=args.report_noop,
        args_diff=args.diff,
    )
    cpu_count = get_cpu_count()
    with ThreadPoolExecutor(max_workers=max(1, int(cpu_count / 2))) as executor:
        futures = [executor.submit(closure, file) for file in args.files]
        results = [f.result() for f in futures]

    for res in results:
        for message in res.messages:
            print(message.content, file=message.dest)

    return max(res.status for res in results)


def _format_single_file_cli(
    file: str, *, args_validate: bool, args_report_noop: bool, args_diff: bool
) -> TaskResults:
    status: Literal[0, 1] = 0
    messages: list[Message] = []

    if not os.path.isfile(file):
        status = 1
        messages.append(Message(f"Error: could not find {file}", sys.stderr))
        return TaskResults(status, messages)

    if args_validate:
        try:
            validate_baseline = load(file)
        except ValueError as exc:
            status = 1
            messages.append(Message(f"Error: {exc}", sys.stderr))
            return TaskResults(status, messages)

    with open(file, mode="rb") as fh:
        data = fh.read().decode("utf-8")
        # make sure newlines are always decoded as \n, even on windows
        data = data.replace("\r\n", "\n")

    fmted_data = format_string(data)

    if fmted_data == data:
        if args_report_noop:
            # printing to stderr so that we can pipe into cdiff in --diff mode
            messages.append(Message(f"{file} is already formatted", sys.stderr))
        return TaskResults(status, messages)

    if args_diff:
        diff = "\n".join(
            line.removesuffix("\n")
            for line in unified_diff(
                data.splitlines(), fmted_data.splitlines(), fromfile=file
            )
        )
        if diff:
            status = 1
            messages.append(Message(diff, sys.stdout))
    else:
        status = 1
        messages.append(Message(f"Fixing {file}", sys.stderr))
        if not os.access(file, os.W_OK):
            messages.append(
                Message(
                    f"Error: could not write to {file} (permission denied)", sys.stderr
                )
            )
            return TaskResults(status, messages)

        with TemporaryDirectory(dir=os.path.dirname(file)) as tmpdir:
            tmpfile = os.path.join(tmpdir, "ini")
            with open(tmpfile, "wb") as bfh:
                bfh.write(fmted_data.encode("utf-8"))

            if args_validate and load(tmpfile) != validate_baseline:  # pragma: no cover
                messages.append(
                    Message(
                        f"Error: failed to format {file}: "
                        "formatted data compares unequal to unformatted data",
                        sys.stderr,
                    )
                )
                return TaskResults(status, messages)

            # this may still raise an error in the unlikely case of a race condition
            # (if permissions are changed between the look and the leap), but we
            # won't try to catch it unless it happens in production, because it is
            # difficult to test systematically.
            os.replace(tmpfile, file)

    return TaskResults(status, messages)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
