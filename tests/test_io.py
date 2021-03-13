from inifix.io import dump, load


def test_load(inifile):
    conf = load(inifile)

    assert all([isinstance(name, str) for name in conf])
    assert all([isinstance(body, dict) for body in conf.values()])
    for body in conf.values():
        assert all([isinstance(param, str) for param in body])


def test_dump_known_files(inifile, tmp_path):
    conf = load(inifile)

    file = tmp_path / "save.ini"
    dump(conf, file)

    # a little weak but better than just testing that the file isn't empty
    new_body = file.read_text()
    for section_name in conf:
        assert f"[{section_name}]\n" in new_body
