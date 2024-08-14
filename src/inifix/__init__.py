from .io import dump
from .io import dumps
from .io import load
from .io import loads
from .validation import validate_inifile_schema
from .format import format_string

from importlib.metadata import version

__version__ = version("inifix")
del version
