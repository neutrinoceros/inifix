from importlib.metadata import version

import inifix


def test_dunder_version():
    assert inifix.__version__ == version("inifix")


def test_dunder_version_tuple():
    vt = inifix.__version_tuple__
    assert isinstance(vt, tuple)
    assert len(vt) == 3
    assert ".".join(str(i) for i in vt) == version("inifix")
