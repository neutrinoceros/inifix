import re
import sys
from enum import Enum, auto
from typing import Literal

from inifix._typing import AnyConfig

if sys.version_info >= (3, 11):
    from typing import assert_never
else:
    from exceptiongroup import ExceptionGroup
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


def collect_exceptions_for_elementary_item(
    key: object, value: object
) -> list[ValueError]:
    """
    Collect exceptions for the given key/value pair.
    """
    exceptions: list[ValueError] = []
    if not isinstance(key, str):
        exceptions.append(
            ValueError(
                f"Found key {key} with type {type(key).__name__}. Expected a str"
            )
        )
        return exceptions

    if len(key) == 0:
        exceptions.append(ValueError("Found an empty str as key"))
    elif _uses_invalid_chars(key):
        exceptions.append(
            ValueError(
                f"Found key {key!r}, "
                "expected only alphanumeric characters or special characters from {'-', '.'}"
            )
        )
    elif not key[0].isalpha():
        exceptions.append(
            ValueError(f"Found key {key!r}. Keys are expected to start with a letter")
        )

    invalid_values: list[object] = []
    if isinstance(value, list):
        for ev in value:  # pyright: ignore[reportUnknownVariableType]
            if not isinstance(ev, SCALAR_TYPES):
                invalid_values.append(ev)  # pyright: ignore[reportUnknownArgumentType]
    elif not isinstance(value, SCALAR_TYPES):
        invalid_values.append(value)

    if len(invalid_values) == 1:
        exceptions.append(
            ValueError(
                f"Key {key!r} is associated to value {value} "
                f"with type {type(value).__name__}. "  # pyright: ignore[reportUnknownArgumentType]
                "Expected an int, float, bool, str, or list of these types"
            )
        )
    elif invalid_values:
        exceptions.append(
            ValueError(
                f"Key {key!r} is associated to values {invalid_values} with types "
                f"[{', '.join(type(v).__name__ for v in invalid_values)}], respectively. "
                "Expected only int, float, bool and str values"
            )
        )
    return exceptions


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

    section_to_exceptions: dict[str, list[ValueError]] = {}

    for k, v in data.items():
        if not isinstance(k, str):
            raise ValueError(
                f"Invalid schema: found key {k} with type {type(k).__name__}, expected a str"
            )

        if isinstance(v, dict):
            match sections_mode:
                case SectionsMode.ALLOW | SectionsMode.REQUIRE:
                    section_exceptions: list[ValueError] = []
                    for kk, vv in v.items():
                        section_exceptions.extend(
                            collect_exceptions_for_elementary_item(kk, vv)
                        )
                    if section_exceptions:
                        section_to_exceptions[k] = section_exceptions
                case SectionsMode.FORBID:
                    raise ValueError(
                        "Invalid schema: sections were explicitly forbidden, "
                        f"but one was found under key {k!r}"
                    )
                case _ as unreachable:
                    assert_never(sections_mode)

        else:
            match sections_mode:
                case SectionsMode.ALLOW | SectionsMode.FORBID:
                    section_exceptions = collect_exceptions_for_elementary_item(k, v)
                    if section_exceptions:
                        section_to_exceptions[k] = section_exceptions
                case SectionsMode.REQUIRE:
                    raise ValueError(
                        "Invalid schema: sections were explicitly required, "
                        "but the following key/value pair was found outside of "
                        f"any section: '{k}', {v}"
                    )
                case _ as unreachable:
                    assert_never(unreachable)

    groups: list[ExceptionGroup[ValueError]] = []
    for section, exceptions in section_to_exceptions.items():
        groups.append(ExceptionGroup(f"Section '{section}' is invalid", exceptions))
    if groups:
        raise ExceptionGroup("Invalid schema", groups)
