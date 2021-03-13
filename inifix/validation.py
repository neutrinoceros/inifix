from more_itertools import always_iterable


def validate_inifile_schema(d: dict, /) -> None:
    """
    Raise `ValueError` if and only if the argument is not a
    valid configuration according to Pluto's specifications.
    """
    err = ValueError("Invalid schema detected.")
    for section, content in d.items():
        if not isinstance(section, str):
            raise err
        if not isinstance(content, dict):
            raise err
        for name, values in content.items():
            if not isinstance(name, str):
                raise err
            for val in always_iterable(values):
                if not isinstance(val, (int, float, bool, str)):
                    raise err
