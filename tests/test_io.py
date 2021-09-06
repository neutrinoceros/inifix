import pytest

from inifix.io import dump
from inifix.io import load


@pytest.mark.parametrize(
    "mode,expected_err",
    [("rt", FileNotFoundError), ("rb", FileNotFoundError), ("wb", TypeError)],
)
def test_dump_wrong_mode(mode, expected_err, inifile, tmp_path):
    conf = load(inifile)
    save_file = str(tmp_path / "save.ini")
    with pytest.raises(expected_err):
        with open(save_file, mode=mode) as fh:
            dump(conf, fh)


def test_dump_to_file_descriptor(inifile, tmp_path):
    conf = load(inifile)

    file = tmp_path / "save.ini"
    with open(file, mode="w") as fh:
        dump(conf, fh)

    # a little weak but better than just testing that the file isn't empty
    new_body = file.read_text()
    for key, val in conf.items():
        if isinstance(val, dict):
            assert f"[{key}]\n" in new_body


def test_dump_to_file_path(inifile, tmp_path):
    conf = load(inifile)

    # pathlib.Path obj
    file1 = tmp_path / "save1.ini"
    dump(conf, file1)
    body1 = file1.read_text()

    # str
    file2 = str(tmp_path / "save2.ini")
    dump(conf, file2)
    body2 = open(file2).read()

    assert body1 == body2
    for key, val in conf.items():
        if isinstance(val, dict):
            assert f"[{key}]\n" in body2


def test_load_empty_file(capsys, tmp_path):
    target = tmp_path / "empty_file"
    target.touch()
    with pytest.raises(ValueError):
        load(target)
