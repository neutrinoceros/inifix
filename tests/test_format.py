import os
import shutil
from pathlib import Path
from stat import S_IREAD
from subprocess import run

import pytest

from inifix import load
from inifix.format import iniformat
from inifix.format import main

DATA_DIR = Path(__file__).parent / "data"


def test_format_keep_data(inifile, capsys, tmp_path):
    target = tmp_path / inifile.name

    ref_data = load(inifile)
    shutil.copyfile(inifile, target)

    ret = main([str(target)])
    assert isinstance(ret, int)

    out, err = capsys.readouterr()

    assert out == ""
    data_new = load(target)
    assert data_new == ref_data


@pytest.mark.parametrize("infile", ("format-in.ini", "format-out.ini"))
def test_exact_format_diff(infile, capsys, tmp_path):
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
    assert (ret == 0 and out == "") or (ret != 0 and err == "" and expected in out)


def test_exact_format_inplace(capsys, tmp_path):
    DATA_DIR = Path(__file__).parent / "data"
    target = tmp_path / "out.ini"
    shutil.copyfile(DATA_DIR / "format-in.ini", target)

    ret = main([str(target)])
    out, err = capsys.readouterr()

    assert err == f"Fixing {target}\n"
    assert ret != 0

    expected = (DATA_DIR / "format-out.ini").read_text()
    res = target.read_text()
    assert res == expected


def test_no_parameters(capsys, tmp_path):
    target = tmp_path / "no_params.ini"
    target.write_text(
        "    # comment 1\n"
        "[Section A]\n"
        "  # comment 2\n"
        " # comment 3\n"
        "[Section B]"
    )
    ret = main([str(target)])
    assert ret != 0

    expected = (
        "# comment 1\n"
        "\n"
        "[Section A]\n"
        "# comment 2\n"
        "# comment 3\n"
        "\n"
        "[Section B]\n"
    )
    assert target.read_text() == expected


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
    assert f"Error: {str(target)!r} appears to be empty.\n" in err


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

    assert (ret == 0 and out == "") or (ret != 0 and err == "" and out != "")


def test_report_noop(capsys, tmp_path):
    inifile = DATA_DIR / "format-out.ini"
    target = tmp_path / inifile.name

    shutil.copyfile(inifile, target)

    ret = main([str(target), "--report-noop"])
    assert ret == 0

    out, err = capsys.readouterr()

    assert out == ""
    assert err == f"{target} is already formatted\n"
