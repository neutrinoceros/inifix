import textwrap
from pathlib import Path

import pytest
from _pytest.fixtures import SubRequest
from runtime_introspect import runtime_feature_set

DATA_DIR = Path(__file__).parent / "data"
INIFILES_PATHS = list(DATA_DIR.glob("*.ini")) + list(DATA_DIR.glob("*.cfg"))
INIFILES_IDS = [inifile.name[:-4] for inifile in INIFILES_PATHS]

INIFILES: dict[Path, str] = dict(zip(INIFILES_PATHS, INIFILES_IDS, strict=True))

INIFILES_W_SECTIONS = {
    path: id
    for path, id in INIFILES.items()
    if "fargo" not in id and path.suffix != ".cfg"
}
INIFILES_WO_SECTIONS = {
    path: id for path, id in INIFILES.items() if path not in INIFILES_W_SECTIONS
}


@pytest.fixture()
def datadir() -> Path:
    return DATA_DIR


@pytest.fixture(
    params=list(INIFILES.keys()),
    ids=list(INIFILES.values()),
)
def inifile(request: SubRequest) -> Path:
    return Path(request.param)


@pytest.fixture(
    params=list(INIFILES_W_SECTIONS.keys()),
    ids=list(INIFILES_W_SECTIONS.values()),
)
def inifile_with_sections(request: SubRequest) -> Path:
    return Path(request.param)


@pytest.fixture(
    params=list(INIFILES_WO_SECTIONS.keys()),
    ids=list(INIFILES_WO_SECTIONS.values()),
)
def inifile_without_sections(request: SubRequest) -> Path:
    return Path(request.param)


def pytest_report_header(config: pytest.Config, start_path: Path) -> list[str]:
    fs = runtime_feature_set()
    diagnostics = fs.diagnostics(features=["free-threading", "JIT"])
    return [
        "Runtime optional features state (snapshot):",
        textwrap.indent("\n".join(diagnostics), "  "),
    ]
