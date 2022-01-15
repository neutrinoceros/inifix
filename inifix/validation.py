import re
from typing import Any
from typing import Mapping

from more_itertools import always_iterable

_PARAM_NAME_REGEXP = re.compile(r"[-\w]+")
SCALAR_TYPES = (int, float, bool, str)


def _uses_invalid_chars(s: str) -> bool:
    ma = re.fullmatch(_PARAM_NAME_REGEXP, s)
    return ma is None


def validate_elementary_item(key: Any, value: Any) -> None:
    if not isinstance(key, str):
        raise ValueError(
            f"Invalid schema: received key '{key}' with type '{type(key)}', "
            "expected a str"
        )
    if len(key) == 0:
        raise ValueError("Invalid schema: received an empty str as key")
    if _uses_invalid_chars(key):
        raise ValueError(
            f"Invalid schema: received key {key!r}, "
            "expected only alphanumeric characters or '-'"
        )
    if not key[0].isalpha():
        raise ValueError(
            f"Invalid schema: received key {key!r}, "
            "keys are expected to start with a letter"
        )
    if not isinstance(value, (*SCALAR_TYPES, list)):
        raise ValueError(
            f"Invalid schema: received value with type '{type(value)}', "
            "exepected an int, float, bool, str, or list"
        )
    for ev in always_iterable(value):
        if not isinstance(ev, SCALAR_TYPES):
            raise ValueError(
                f"Invalid schema: reveived value '{value}' with type '{type(value)}', "
                "exepected a int, float, bool or str"
            )


def validate_inifile_schema(d: Mapping, /) -> None:
    """
    Raise `ValueError` if and only if the argument is not a
    valid configuration.
    """

    for k, v in d.items():
        if not isinstance(k, str):
            raise ValueError(
                f"Invalid schema: received key '{k}' with type '{type(k)}', expected a str"
            )
        if isinstance(v, dict):
            for kk, vv in v.items():
                validate_elementary_item(kk, vv)
        else:
            validate_elementary_item(k, v)
