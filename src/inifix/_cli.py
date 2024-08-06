from __future__ import annotations

from typing import Literal, NamedTuple, TextIO


class Message(NamedTuple):
    content: str
    dest: TextIO


class TaskResults(NamedTuple):
    status: Literal[0, 1]
    messages: list[Message]
