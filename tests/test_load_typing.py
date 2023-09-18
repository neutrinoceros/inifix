from pathlib import Path
from typing import TypedDict

import pytest

import inifix

DATA_DIR = Path(__file__).parent / "data"


def test_return_type() -> None:
    # this is mostly a textbook example of the expected usage of `return_type`
    class DummySection(TypedDict):
        x: int
        y: int
        z: int
        origin: list[int]
        fast: bool
        pi: float
        timestep: float

    class Expected(TypedDict):
        Dummy: DummySection

    ret: Expected = inifix.load(DATA_DIR / "minimal.ini", return_type=Expected)

    dum = ret["Dummy"]
    dum["x"]
    dum["y"].as_integer_ratio()


def test_inconsistent_return_type() -> None:
    # the way this test works is by relying on mypy's configuration details:
    # unused 'type: ignore' comments are flagged, so the only way to pass here is if
    # the 'assignment' error is actually raised
    _ret: int = inifix.load(DATA_DIR / "minimal.ini", return_type=float)  # type: ignore[assignment]


def test_incorrect_return_type() -> None:
    # even specifying an incorrect return type should type-check
    # (this is the responsibility of the user)
    class Expected(TypedDict):
        this_key_does_not_exist: int

    ret: Expected = inifix.load(DATA_DIR / "idefix-khi.ini", return_type=Expected)

    # ... but it should fail at runtime
    with pytest.raises(KeyError):
        ret["this_key_does_not_exist"]
