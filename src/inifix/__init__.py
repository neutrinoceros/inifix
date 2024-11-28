from __future__ import annotations

from .io import dump
from .io import dumps
from .io import load
from .io import loads
from .validation import validate_inifile_schema
from .format import format_string

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any


def __getattr__(name: str) -> Any:
    if name == "__version__":
        from importlib.metadata import version

        return version("inifix")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


del TYPE_CHECKING
