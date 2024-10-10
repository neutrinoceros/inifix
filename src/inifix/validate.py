from __future__ import annotations

import argparse
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import Literal

from inifix._cli import Message, TaskResults, get_cpu_count
from inifix.io import load


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+")

    args = parser.parse_args(argv)
    closure = _validate_single_file_cli
    cpu_count = get_cpu_count()
    with ThreadPoolExecutor(max_workers=max(1, int(cpu_count / 2))) as executor:
        futures = [executor.submit(closure, file) for file in args.files]
        results = [f.result() for f in futures]

    for res in results:
        for message in res.messages:
            print(message.content, file=message.dest)

    return max(res.status for res in results)


def _validate_single_file_cli(file: str) -> TaskResults:
    status: Literal[0, 1] = 0
    messages: list[Message] = []
    if not os.path.isfile(file):
        status = 1
        messages.append(Message(f"Error: could not find {file}", sys.stderr))
        return TaskResults(status, messages)
    try:
        load(file)
    except ValueError as exc:
        status = 1
        messages.append(Message(f"Failed to validate {file}:\n  {exc}", sys.stderr))
    else:
        messages.append(Message(f"Validated {file}", sys.stdout))
    return TaskResults(status, messages)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
