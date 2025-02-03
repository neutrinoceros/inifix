import warnings


def iniformat(s: str, /) -> str:
    from inifix._format import format_string

    warnings.warn(
        "inifix.format.iniformat is deprecated since v5.0.0 "
        "and will be removed in a future version. "
        "Please use inifix.format_string instead.",
        category=DeprecationWarning,
        stacklevel=2,
    )
    return format_string(s)
