from inifix.iniconf import InifixConf


def test_pluto_disk_planet(datadir):
    conf = InifixConf(datadir / "pluto-DiskPlanet.ini")
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
