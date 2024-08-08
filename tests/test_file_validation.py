import pytest

from inifix.validate import main


@pytest.fixture(
    params=[
        pytest.param("a\n", id="missing value (empty row)"),
        pytest.param("a #\n", id="missing value (comm)"),
        pytest.param(r"/!\\\n", id="invalid param name (special chars)"),
        pytest.param("100 100\n", id="invalid param name (num-1)"),
        pytest.param("1e2 100\n", id="invalid param name (num-2)"),
        pytest.param("[Unclosed Section\na 1 2 3\n", id="unclosed section"),
        pytest.param("[[extra left bracket]\na 1 2 3\n", id="mismatched left bracket"),
        pytest.param(
            "[extra right bracket]]\na 1 2 3\n", id="mismatched right bracket"
        ),
        pytest.param("[extra] stuff that's not a comment", id="missing comment char"),
        pytest.param("[()]", id="invalid section chars (parens)"),
        pytest.param("[{}]", id="invalid section chars (brackets)"),
    ]
)
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
