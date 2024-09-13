from __future__ import annotations

import os
import sys
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
    base_cpu_count: int | None
    if sys.version_info >= (3, 13):
        base_cpu_count = os.process_cpu_count()
    else:
        if hasattr(os, "sched_getaffinity"):
            # this function isn't available on all platforms
            base_cpu_count = len(os.sched_getaffinity(0))
        else:
            # this proxy is good enough in most situations
            base_cpu_count = os.cpu_count()
    return base_cpu_count or 1
