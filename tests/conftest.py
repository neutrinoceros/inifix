from pathlib import Path

import pytest
from more_itertools import unzip

DATA_DIR = Path(__file__).parent / "data"
INIFILES = list(DATA_DIR.glob("*.ini"))
INIFILES_IDS = [inifile.name[:-4] for inifile in INIFILES]


@pytest.fixture(params=INIFILES, ids=INIFILES_IDS)
def inifile(request):
    return request.param


INVADLID_SCHEMAS, INVALID_SCHEMAS_IDS = unzip(
    (
        ({1: {"param": 1}}, "section_no_str"),
        ({"param": 1}, "content_no_dict"),
        ({"section": {1: "one"}}, "param_name_no_str"),
        ({"section": {"param": [[1, 2], [3, 4]]}}, "non_flat_sequence"),
    )
)


@pytest.fixture(params=INVADLID_SCHEMAS, ids=INVALID_SCHEMAS_IDS)
def invalid_conf(request):
    return request.param
