from _pytest.fixtures import SubRequest
from pathlib import Path

import pytest

DATA_DIR = Path(__file__).parents[3] / "tests" / "data"
INIFILES_PATHS = list(DATA_DIR.glob("*.ini")) + list(DATA_DIR.glob("*.cfg"))
INIFILES_IDS = [inifile.name[:-4] for inifile in INIFILES_PATHS]

INIFILES: dict[Path, str] = dict(zip(INIFILES_PATHS, INIFILES_IDS, strict=True))


@pytest.fixture()
def datadir_root() -> Path:
    if not DATA_DIR.exists():  # pragma: no cover
        pytest.skip("test data isn't available")

    return DATA_DIR


@pytest.fixture(params=list(INIFILES.keys()), ids=list(INIFILES.values()))
def inifile_root(request: SubRequest) -> Path:
    return Path(request.param)
