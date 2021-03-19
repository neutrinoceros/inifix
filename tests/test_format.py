import os
import shutil
from pathlib import Path
from stat import S_IREAD

import pytest

from inifix import load
from inifix.format import main


@pytest.mark.parametrize("flag", ["-i", "--inplace"])
def test_format_keep_data(flag, inifile, capsys, tmp_path):
    target = tmp_path / inifile.name
    data_ref = load(inifile)
    shutil.copyfile(inifile, target)

    ret = main([str(target), flag])
    assert ret == 0
    out, err = capsys.readouterr()
    assert out == ""
    assert err == ""

    data_new = load(target)
    assert data_new == data_ref


@pytest.mark.parametrize("flag", ["-i", "--inplace"])
def test_exact_format(flag, capsys, tmp_path):
    DATA_DIR = Path(__file__).parent / "data"
    target = tmp_path / "out.ini"
    shutil.copyfile(DATA_DIR / "format-in.ini", target)
    ret = main([str(target), flag])
    assert ret == 0
    out, err = capsys.readouterr()
    assert out == ""
    assert err == ""
    expected = (DATA_DIR / "format-out.ini").read_text()
    res = target.read_text()
    assert res == expected


def test_missing_file(capsys, tmp_path):
    target = tmp_path / "not_a_file"
    ret = main([str(target)])
    assert ret != 0
    out, err = capsys.readouterr()
    assert out == ""
    assert err == f"Error: could not find {target}\n"


def test_empty_file(capsys, tmp_path):
    target = tmp_path / "invalid_file"
    target.touch()
    ret = main([str(target)])
    assert ret != 0
    out, err = capsys.readouterr()
    assert out == ""
    assert err == f"Error: {target} appears to be emtpy.\n"


def test_error_read_only_file(inifile, capsys, tmp_path):
    target = tmp_path / inifile.name
    shutil.copy(inifile, target)
    os.chmod(target, S_IREAD)

    ret = main([str(target), "--inplace"])
    assert ret != 0
    out, err = capsys.readouterr()
    assert out == ""
    assert err == f"Error: could not write to {target}\n"


def test_write_to_console(inifile, capsys, tmp_path):
    target = tmp_path / inifile.name
    shutil.copy(inifile, target)
    # format the file for easier comparison
    ret = main([str(target), "--inplace"])

    ret = main([str(target)])
    assert ret == 0
    out, err = capsys.readouterr()
    assert out == target.read_text() + "\n"
    assert err == f"{target} >>>\n"
