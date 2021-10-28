import re

from more_itertools import always_iterable

from inifix._deprecation import future_positional_only

_PARAM_NAME_REGEXP = re.compile(r"[-\w]+")


def _uses_invalid_chars(s: str) -> bool:
    ma = re.fullmatch(_PARAM_NAME_REGEXP, s)
    return ma is None


def validate_elementary_item(key, value) -> None:
    scalar_types = (int, float, bool, str)
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
    if not isinstance(value, (*scalar_types, list)):
        raise ValueError(
            f"Invalid schema: received value with type '{type(value)}', "
            "exepected an int, float, bool, str, or list"
        )
    for ev in always_iterable(value):
        if not isinstance(ev, scalar_types):
            raise ValueError(
                f"Invalid schema: reveived value '{value}' with type '{type(value)}', "
                "exepected a int, float, bool or str"
            )


@future_positional_only({0: "d"})
def validate_inifile_schema(d: dict) -> None:
    """
    Raise `ValueError` if and only if the argument is not a
    valid configuration according to `inifix.InifixConf` specifications.
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
