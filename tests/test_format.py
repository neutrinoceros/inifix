import os
import shutil
import sys
from pathlib import Path
from stat import S_IREAD
from subprocess import run

import pytest

from inifix import load
from inifix.format import iniformat
from inifix.format import main


def test_format_keep_data(inifile, capsys, tmp_path):
    target = tmp_path / inifile.name

    ref_data = load(inifile)
    shutil.copyfile(inifile, target)

    ret = main([str(target)])
    assert isinstance(ret, int)

    out, err = capsys.readouterr()

    # nothing to output to stdout with --inplace
    assert out == ""
    if err == f"{target} is already formatted\n":
        assert ret == 0
    else:
        assert err == f"Fixing {target}\n"
        assert ret != 0

    data_new = load(target)
    assert data_new == ref_data


@pytest.mark.skipif(
    sys.version_info < (3, 7), reason="need capture_output argument in subprocess.run"
)
@pytest.mark.parametrize("infile", ("format-in.ini", "format-out.ini"))
def test_exact_format_diff(infile, capsys, tmp_path):
    DATA_DIR = Path(__file__).parent / "data"

    expected = "\n".join(
        run(
            [
                "diff",
                "-u",
                str(DATA_DIR / "format-in.ini"),
                str(DATA_DIR / "format-out.ini"),
            ],
            capture_output=True,
        )
        .stdout.decode()
        .splitlines()[2:]
    )

    target = tmp_path / "out.ini"
    shutil.copyfile(DATA_DIR / infile, target)

    ret = main([str(target), "--diff"])
    out, err = capsys.readouterr()

    if err == f"{target} is already formatted\n":
        assert ret == 0
        assert out == ""
    else:
        assert err == ""
        assert ret != 0
        assert expected in out


def test_exact_format_inplace(capsys, tmp_path):
    DATA_DIR = Path(__file__).parent / "data"
    target = tmp_path / "out.ini"
    shutil.copyfile(DATA_DIR / "format-in.ini", target)

    ret = main([str(target)])
    out, err = capsys.readouterr()

    if err == f"{target} is already formatted\n":
        assert ret == 0
    else:
        assert err == f"Fixing {target}\n"
        assert ret != 0

    expected = (DATA_DIR / "format-out.ini").read_text()
    res = target.read_text()
    assert res == expected


@pytest.mark.parametrize("size", ["10", "20", "50"])
def test_exact_format_with_column_size_flag(size, capsys, tmp_path):
    DATA_DIR = Path(__file__).parent / "data"
    target = tmp_path / "out.ini"
    shutil.copyfile(DATA_DIR / "format-column-size-in.ini", target)

    ret = main([str(target), "--name-column-size", size])
    out, err = capsys.readouterr()

    assert f"Fixing {target}\n" in err
    assert ret != 0

    expected = (DATA_DIR / f"format-column-size-out-{size}.ini").read_text()
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
    assert f"Error: {target} appears to be emtpy.\n" in err


def test_error_read_only_file(inifile, capsys, tmp_path):
    target = tmp_path / inifile.name
    shutil.copy(inifile, target)

    data = target.read_text()
    if iniformat(data) == data:
        return

    os.chmod(target, S_IREAD)

    ret = main([str(target)])
    assert ret != 0
    out, err = capsys.readouterr()
    assert out == ""
    assert f"Error: could not write to {target}\n" in err


def test_diff_stdout(inifile, capsys, tmp_path):
    target = tmp_path / inifile.name
    shutil.copy(inifile, target)

    ret = main([str(target), "--diff"])
    # we can't predict if formatting is needed
    assert isinstance(ret, int)
    out, err = capsys.readouterr()

    if err == f"{target} is already formatted\n":
        assert ret == 0
        assert out == ""
    else:
        assert err == ""
        assert ret != 0
        assert out != ""
