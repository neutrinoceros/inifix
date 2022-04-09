import pytest
from more_itertools import unzip

from inifix.validate import main

INVALID_CONTENTS, INVALID_CONTENTS_IDS = unzip(
    (
        ("a\n", "missing value (empty row)"),
        ("a #\n", "missing value (comm)"),
        (r"/!\\\n", "invalid param name (special chars)"),
        ("100 100\n", "invalid param name (num-1)"),
        ("1e2 100\n", "invalid param name (num-2)"),
        ("[Unclosed Section\na 1 2 3\n", "unclosed section"),
        ("[[extra left bracket]\na 1 2 3\n", "mismatched left bracket"),
        ("[extra right bracket]]\na 1 2 3\n", "mismatched right bracket"),
        ("[extra] stuff that's not a comment", "missing comment char"),
        ("[()]", "invalid section chars (parens)"),
        ("[{}]", "invalid section chars (brackets)"),
    )
)


@pytest.fixture(params=INVALID_CONTENTS, ids=INVALID_CONTENTS_IDS)
def invalid_file(tmp_path, request):
    file = tmp_path / "myfile.ini"
    file.write_text(request.param)
    return file


def test_empty_file(capsys, tmp_path):
    target = tmp_path / "invalid_file"
    target.touch()
    ret = main([str(target)])
    assert ret != 0
    out, err = capsys.readouterr()
    assert out == ""
    assert f"Failed to validate {target}:" in err
    assert "appears to be empty.\n" in err


def test_missing_file(capsys, tmp_path):
    target = tmp_path / "not_a_file"
    ret = main([str(target)])
    assert ret != 0
    out, err = capsys.readouterr()
    assert out == ""
    assert f"Error: could not find {target}" in err


def test_invalid_files(invalid_file, capsys):
    ret = main([str(invalid_file)])

    stdout, stderr = capsys.readouterr()

    assert stdout == ""
    assert stderr.startswith("Failed to validate")
    assert ret != 0


def test_valid_files(inifile, capsys):
    ret = main([str(inifile)])

    stdout, stderr = capsys.readouterr()

    assert stdout == f"Validated {inifile}\n"
    assert stderr == ""
    assert ret == 0
