import sys
from pathlib import Path

import pytest

DATA_DIR = Path(__file__).parent / "data"
INIFILES_PATHS = list(DATA_DIR.glob("*.ini")) + list(DATA_DIR.glob("*.cfg"))
INIFILES_IDS = [inifile.name[:-4] for inifile in INIFILES_PATHS]

INIFILES = dict(zip(INIFILES_PATHS, INIFILES_IDS, strict=True))

INIFILES_W_SECTIONS = {
    path: id
    for path, id in INIFILES.items()
    if "fargo" not in id and path.suffix != ".cfg"
}
INIFILES_WO_SECTIONS = {
    path: id for path, id in INIFILES.items() if path not in INIFILES_W_SECTIONS
}


@pytest.fixture()
def datadir():
    return DATA_DIR


@pytest.fixture(params=INIFILES.keys(), ids=INIFILES.values())
def inifile(request):
    return request.param


@pytest.fixture(params=INIFILES_W_SECTIONS.keys(), ids=INIFILES_W_SECTIONS.values())
def inifile_with_sections(request):
    return request.param


@pytest.fixture(params=INIFILES_WO_SECTIONS.keys(), ids=INIFILES_WO_SECTIONS.values())
def inifile_without_sections(request):
    return request.param


def pytest_report_header(config, start_path):
    if sys.version_info >= (3, 13):
        is_gil_enabled = sys._is_gil_enabled()
    else:
        is_gil_enabled = True

    return [
        f"{is_gil_enabled = }",
    ]
