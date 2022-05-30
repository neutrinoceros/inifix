from __future__ import annotations

import argparse
import os
import sys

from inifix.io import load


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+")

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
            print(f"Failed to validate {file}:\n  {exc}", file=sys.stderr)
            retv = 1
        else:
            print(f"Validated {file}")

    return retv


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
