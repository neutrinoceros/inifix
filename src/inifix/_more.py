from collections.abc import Iterator

from inifix._typing import Scalar


def always_iterable(obj: Scalar | list[Scalar], /) -> Iterator[Scalar]:
    # adapted from more_iterools 10.1.0 (MIT)
    if isinstance(obj, str):
        return iter((obj,))

    if isinstance(obj, list):
        return iter(obj)
    else:
        return iter((obj,))
