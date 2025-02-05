import sys
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


def pytest_report_header(config, start_path):
    if sys.version_info >= (3, 13):
        is_gil_enabled = sys._is_gil_enabled()
    else:
        is_gil_enabled = True

    return [
        f"{is_gil_enabled = }",
    ]
