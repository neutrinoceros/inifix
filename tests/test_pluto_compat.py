from inifix.idefix_conf import IdefixConf


def test_pluto_disk_planet(datadir):
    conf = IdefixConf(datadir / "pluto-DiskPlanet.ini")
    expected = [
        "Grid",
        "Chombo Refinement",
        "Time",
        "Solver",
        "Boundary",
        "Static_Grid Output",
        "Chombo HDF5 output",
        "Parameters",
    ]
    sections = list(conf.keys())
    assert sections == expected
