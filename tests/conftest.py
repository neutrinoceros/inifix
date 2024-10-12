import sys
from pathlib import Path

import pytest

DATA_DIR = Path(__file__).parent / "data"
INIFILES = list(DATA_DIR.glob("*.ini")) + list(DATA_DIR.glob("*.cfg"))
INIFILES_IDS = [inifile.name[:-4] for inifile in INIFILES]


@pytest.fixture()
def datadir():
    return DATA_DIR


@pytest.fixture(params=INIFILES, ids=INIFILES_IDS)
def inifile(request):
    return request.param


def pytest_report_header(config, start_path):
    if sys.version_info >= (3, 13):
        is_gil_enabled = sys._is_gil_enabled()
    else:
        is_gil_enabled = True

    return [
        f"{is_gil_enabled = }",
    ]
