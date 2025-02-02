import re
import sys
from enum import Enum, auto
from typing import Literal

from inifix._typing import AnyConfig

if sys.version_info >= (3, 11):
    from typing import assert_never
else:
    from typing_extensions import assert_never

_PARAM_NAME_REGEXP = re.compile(r"[-\.\w]+")
SCALAR_TYPES = (int, float, bool, str)


class SectionsMode(Enum):
    ALLOW = auto()
    FORBID = auto()
    REQUIRE = auto()


def _uses_invalid_chars(s: str) -> bool:
    ma = re.fullmatch(_PARAM_NAME_REGEXP, s)
    return ma is None


def validate_elementary_item(key: object, value: object) -> None:
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
            "expected only alphanumeric characters or special characters from {'-', '.'}"
        )
    if not key[0].isalpha():
        raise ValueError(
            f"Invalid schema: received key {key!r}, "
            "keys are expected to start with a letter"
        )
    if isinstance(value, list):
        for ev in value:  # pyright: ignore[reportUnknownVariableType]
            if not isinstance(ev, SCALAR_TYPES):
                raise ValueError(
                    f"Invalid schema: received value '{ev}' with type '{type(ev)}', "  # pyright: ignore[reportUnknownArgumentType]
                    "expected an int, float, bool or str"
                )
    elif not isinstance(value, SCALAR_TYPES):
        raise ValueError(
            f"Invalid schema: received value with type '{type(value)}', "
            "expected an int, float, bool, str, or list"
        )


def validate_inifile_schema(
    data: AnyConfig,
    /,
    *,
    sections: Literal["allow", "forbid", "require"] = "allow",
) -> None:
    """
    Validate structure of a dictionary as an inifix-compliant configuration.

    Parameters
    ----------
    data: dict
      the candidate configuration to be (in)validated.

    sections: 'allow' (default), 'forbid' or 'require'
      use sections='forbid' to invalidate any section found,
      or sections='require' to invalidate a sectionless structure.
      Default mode (sections='allow') permits both.

      .. versionadded: 5.1.0

    Raises
    ------
    TypeError: for unrecognized values in parameter sections.
    ValueError: if and only if data does not conform to the expected schema.

    """
    match sections:
        case "allow":
            sections_mode = SectionsMode.ALLOW
        case "forbid":
            sections_mode = SectionsMode.FORBID
        case "require":
            sections_mode = SectionsMode.REQUIRE
        case _:
            raise TypeError(
                "Unknown value for parameter sections. "
                f"Got {sections=!r}, expected 'allow', 'forbid' or 'require'"
            )

    for k, v in data.items():
        if not isinstance(k, str):
            raise ValueError(
                f"Invalid schema: received key '{k}' "
                f"with type '{type(k)}', expected a str"
            )

        if isinstance(v, dict):
            match sections_mode:
                case SectionsMode.ALLOW | SectionsMode.REQUIRE:
                    for kk, vv in v.items():
                        validate_elementary_item(kk, vv)
                case SectionsMode.FORBID:
                    raise ValueError(
                        "Invalid schema: sections were explicitly forbidden, "
                        f"but one was found under key '{k}'"
                    )
                case _:  # pragma: no cover
                    assert_never(sections_mode)

        else:
            match sections_mode:
                case SectionsMode.ALLOW | SectionsMode.FORBID:
                    validate_elementary_item(k, v)
                case SectionsMode.REQUIRE:
                    raise ValueError(
                        "Invalid schema: sections were explicitly required, "
                        "but the following key/value pair was found outside of "
                        f"any section: '{k}', {v}"
                    )
                case _:  # pragma: no cover
                    assert_never(sections_mode)
