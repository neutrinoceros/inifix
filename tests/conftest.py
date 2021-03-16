from pathlib import Path

import pytest

DATA_DIR = Path(__file__).parent / "data"
INIFILES = list(DATA_DIR.glob("*.ini"))
INIFILES_IDS = [inifile.name[:-4] for inifile in INIFILES]


@pytest.fixture()
def datadir():
    return DATA_DIR


@pytest.fixture(params=INIFILES, ids=INIFILES_IDS)
def inifile(request):
    return request.param
