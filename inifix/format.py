import argparse
import os
import re
import sys
from typing import Optional
from typing import Sequence

from inifix.io import load

NAME_COL_MINSIZE = 10
COMMENT_COL = 80


def _normalize_whitespace(s: str) -> str:
    return re.sub(r"\s", " ", s).strip()


def iniformat(data: str) -> str:
    lines = data.splitlines()
    contents = []
    comments = []
    for line in lines:
        content, _, comment = line.partition("#")
        contents.append(_normalize_whitespace(content))
        comments.append(_normalize_whitespace(comment))

    # comment_col = max(80, len(max(contents)) + 10)
    max_name_size = max(
        len(c.split()[0]) for c in contents if c and not c.startswith("[")
    )
    name_col_size = max(max_name_size + 4, NAME_COL_MINSIZE)
    new_lines = []
    for content, comment in zip(contents, comments):
        new_line = ""
        offset = 0
        if content:
            if content.startswith("["):
                new_line += f"{content}\n"
            else:
                name, *values = content.split()
                new_line += f"{name.ljust(name_col_size)}    {'  '.join(values)}"
                offset = COMMENT_COL - len(new_line)
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
    parser.add_argument("-i", "--inplace", action="store_true")
    args = parser.parse_args(argv)

    for file in args.files:
        if not os.path.isfile(file):
            print(f"Error: could not find {file}", file=sys.stderr)
            return 1
        try:
            load(file)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

        with open(file) as fh:
            data = fh.read()

        if (fmted_data := iniformat(data)) == data:
            continue

        if args.inplace:
            print(f"Fixing {file}", file=sys.stderr)
            try:
                with open(file, "w") as fh:
                    fh.write(fmted_data)
            except OSError:
                print(f"Error: could not write to {file}", file=sys.stderr)
                return 1
        else:
            print(f"{file} >>>", file=sys.stderr)
            print(fmted_data)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
