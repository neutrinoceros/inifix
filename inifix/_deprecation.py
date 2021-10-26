import warnings
from functools import wraps
from types import FunctionType
from typing import Dict


def future_positional_only(positions2names: Dict[int, str]):
    """Warn users when using a future positional-only argument as keyword.
    Note that positional-only arguments are available from Python 3.8
    See https://www.python.org/dev/peps/pep-0570/
    """

    def outer(func: FunctionType):
        @wraps(func)
        def inner(*args, **kwargs):
            for no, name in sorted(positions2names.items()):
                if name not in kwargs:
                    continue
                msg = (
                    f"using the {name!r} argument as keyword (on position {no}) "
                    "is deprecated and will stop working in a future release. "
                    "Pass the argument as positional to supress this warning."
                )
                warnings.warn(msg, FutureWarning, stacklevel=2)
            return func(*args, **kwargs)

        return inner

    return outer
