import re
from collections.abc import Iterable
from io import StringIO
from typing import IO

from inifix._io import split_tokens

__all__ = ["format_string"]

PADDING_SIZE = 2


def _format_section(data: str) -> str:
    lines = data.splitlines()
    contents: list[str] = []
    comments: list[str] = []
    parameters: list[str] = []
    values: list[list[str]] = []
    for line in lines:
        content, _, comment = line.partition("#")
        content = content.strip()
        if not content and not comment:
            continue
        contents.append(content)
        comments.append(comment.strip())
        if content.startswith("[") or not content:
            continue
        parameter, *value = split_tokens(content)
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

    new_lines: list[str] = []
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
    content: list[str] = []
    for s in _iter_sections(fh):
        content.append(_format_section(s))
    return _finalize("\n".join(content))
