import inifix


def test_fargo_dummy(datadir):
    conf = inifix.load(datadir / "fargo-dummy.ini")
    expected = {
        "x": 1,
        "y": 2,
        "z": 3,
    }
    assert conf == expected
