from collections.abc import Iterator
from typing import Any


def always_iterable(obj: Any, /) -> Iterator[Any]:
    # adapated from more_iterools 10.1.0 (MIT)
    if obj is None:
        return iter(())

    if isinstance(obj, str):
        return iter((obj,))

    try:
        return iter(obj)
    except TypeError:
        return iter((obj,))
