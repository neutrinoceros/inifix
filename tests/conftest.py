import sys
from enum import Enum
from pathlib import Path

import pytest

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


class CPythonFeatureStatus(Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


def pytest_report_header(config, start_path) -> list[str]:
    if sys.implementation.name != "cpython":
        return []  # pragma: no cover

    jit_st: CPythonFeatureStatus
    if sys.version_info >= (3, 14):
        if sys._jit.is_enabled():
            jit_st = CPythonFeatureStatus.ENABLED
        else:
            jit_st = CPythonFeatureStatus.DISABLED
    elif sys.version_info >= (3, 13):
        jit_st = CPythonFeatureStatus.UNKNOWN  # no public API for introspection
    else:
        jit_st = CPythonFeatureStatus.UNAVAILABLE

    free_threading_st: CPythonFeatureStatus
    if sys.version_info >= (3, 13):
        if sys._is_gil_enabled():
            free_threading_st = CPythonFeatureStatus.DISABLED
        else:
            free_threading_st = CPythonFeatureStatus.ENABLED
    else:
        free_threading_st = CPythonFeatureStatus.UNAVAILABLE

    return [
        "CPython optional features:",
        f"  free-threading: {free_threading_st.value}",
        f"  JIT: {jit_st.value}",
    ]
