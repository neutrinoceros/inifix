from inifix.io import load


def test_pluto_disk_planet(datadir):
    conf = load(datadir / "pluto-DiskPlanet.ini")
    expected = [
        "Grid",
        "Chombo Refinement",
        "Time",
        "Solver",
        "Boundary",
        "Static Grid Output",
        "Chombo HDF5 output",
        "Parameters",
    ]
    sections = list(conf.keys())
    assert sections == expected
