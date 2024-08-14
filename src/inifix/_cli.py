from __future__ import annotations

import os
from typing import Literal, NamedTuple, TextIO


class Message(NamedTuple):
    content: str
    dest: TextIO


class TaskResults(NamedTuple):
    status: Literal[0, 1]
    messages: list[Message]


def get_cpu_count() -> int:
    # this function exists primarily to be mocked
    # instead of something we don't own
    return os.cpu_count() or 1
