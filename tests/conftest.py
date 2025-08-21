import sys
import textwrap
from pathlib import Path

import pytest
from runtime_introspect import CPythonFeatureSet

DATA_DIR = Path(__file__).parents[1] / "lib" / "inifix" / "tests" / "data"
INIFILES_PATHS = list(DATA_DIR.glob("*.ini")) + list(DATA_DIR.glob("*.cfg"))
INIFILES_IDS = [inifile.name[:-4] for inifile in INIFILES_PATHS]

INIFILES = dict(zip(INIFILES_PATHS, INIFILES_IDS, strict=True))


@pytest.fixture()
def datadir_root():
    return DATA_DIR


@pytest.fixture(params=INIFILES.keys(), ids=INIFILES.values())
def inifile_root(request):
    return request.param


def pytest_report_header(config, start_path) -> list[str]:
    if sys.implementation.name == "cpython":
        fs = CPythonFeatureSet()
        return [
            "CPython optional features state (snapshot):",
            textwrap.indent("\n".join(fs.diagnostics()), "  "),
        ]
    else:
        return []  # pragma: no cover
