from importlib.metadata import version

import pytest

import inifix


def test_dunder_version():
    assert inifix.__version__ == version("inifix")


def test_unknown_member():
    with pytest.raises(AttributeError):
        inifix.unknown_member  # noqa: B018
