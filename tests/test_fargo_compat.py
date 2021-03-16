from inifix.io import load


def test_fargo_dummy(datadir):
    conf = load(datadir / "fargo-dummy.ini")
    expected = {
        "x": 1,
        "y": 2,
        "z": 3,
    }
    assert conf == expected
