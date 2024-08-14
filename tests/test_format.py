import os
import shutil
from difflib import unified_diff
from pathlib import Path
from stat import S_IREAD

import pytest

import inifix.format
from inifix import load
from inifix.format import format_string, iniformat, main

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


def diff_file(f1: Path, f2: Path) -> str:
    return (
        "\n".join(
            line.removesuffix("\n")
            for line in unified_diff(
                f1.read_text().splitlines(),
                f2.read_text().splitlines(),
                fromfile=str(f1),
                # tofile=str(f2),
            )
        )
        + "\n"
    )


@pytest.mark.parametrize(
    "infile, expect_diff", [("format-in.ini", True), ("format-out.ini", False)]
)
def test_exact_format_diff(infile, expect_diff, capsys):
    body = (DATA_DIR / infile).read_text()

    ret = main([str(DATA_DIR / infile), "--diff"])
    out, err = capsys.readouterr()
    if expect_diff:
        assert ret != 0
        expected = diff_file(DATA_DIR / infile, DATA_DIR / "format-out.ini")
        assert out == expected
        assert err == ""
    else:
        assert ret == 0
        assert out == ""
        assert err == ""

    assert (DATA_DIR / infile).read_text() == body


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


def test_no_parameters(tmp_path):
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
    if format_string(data) == data:
        return

    os.chmod(target, S_IREAD)

    ret = main([str(target)])
    assert ret != 0
    out, err = capsys.readouterr()
    assert out == ""
    assert f"Error: could not write to {target} (permission denied)\n" in err


def test_informat_depr():
    body = (DATA_DIR / "format-in.ini").read_text()
    s1 = format_string(body)
    with pytest.warns(
        DeprecationWarning,
        match="inifix.format.iniformat is deprecated",
    ):
        s2 = iniformat(body)
    assert s2 == s1


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


def test_format_quoted_strings_with_whitespaces(tmp_path):
    target = tmp_path / "spaces.ini"

    inserted = '''Eggs 'Bacon Saussage'     "spam"'''
    expected = """Eggs    'Bacon Saussage'  "spam"\n"""
    target.write_text(inserted)
    ret = main([str(target)])
    assert ret != 0

    assert target.read_text() == expected


def test_data_preservation(inifile, tmp_path):
    # check that perilous string manipulations do not destroy data
    initial_mapping = load(inifile)
    target = tmp_path / inifile.name
    shutil.copyfile(inifile, target)
    main([str(target)])
    round_mapping = load(target)
    assert round_mapping == initial_mapping


def test_single_core(monkeypatch, tmp_path):
    # regression test for gh-251
    target = tmp_path / "spaces.ini"

    inserted = '''Eggs 'Bacon Saussage'     "spam"'''
    target.write_text(inserted)

    monkeypatch.setattr(inifix.format, "get_cpu_count", lambda: 1)
    inifix.format.main([str(target)])
