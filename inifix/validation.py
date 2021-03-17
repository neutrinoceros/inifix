from typing import Sequence


def validate_inifile_schema(d: dict, /) -> None:
    """
    Raise `ValueError` if and only if the argument is not a
    valid configuration according to `inifix.InifixConf` specifications.
    """
    scalar_types = (int, float, bool, str)
    err = ValueError("Invalid schema detected.")
    for k, v in d.items():
        if not isinstance(k, str):
            raise err
        if isinstance(v, dict):
            for kk, vv in v.items():
                if not isinstance(kk, str):
                    raise err
                if isinstance(vv, Sequence):
                    for vvv in vv:
                        if not isinstance(vvv, scalar_types):
                            raise err
                elif not isinstance(vv, scalar_types):
                    raise err
        elif not isinstance(v, scalar_types):
            raise err
