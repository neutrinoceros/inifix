import shutil
from pathlib import Path

import pytest

from inifix.format import main as inifix_format_cli
from inifix.validate import main as inifix_validate_cli

DATA_DIR = Path(__file__).parent / "data"


N_FILES = 257


@pytest.fixture
def unformatted_files(tmp_path):
    in_file = DATA_DIR / "format-in.ini"
    files = []
    for file_no in range(N_FILES):
        new_file = tmp_path / f"{file_no}.ini"
        shutil.copy(in_file, new_file)
        files.append(new_file.resolve())

    yield files


def test_inifix_format_cli(unformatted_files, capsys):
    ret = inifix_format_cli([str(f) for f in unformatted_files])
    assert ret != 0

    out, err = capsys.readouterr()
    assert out == ""

    # order of lines doesn't matter and is not guaranteed
    err_lines = err.splitlines()
    assert set(err_lines) == {f"Fixing {file}" for file in unformatted_files}

    expected = (DATA_DIR / "format-out.ini").read_text()
    for file in unformatted_files:
        body = file.read_text()
        assert body == expected


def test_inifix_validate_cli(unformatted_files, capsys):
    ret = inifix_validate_cli([str(f) for f in unformatted_files])
    assert ret == 0

    out, err = capsys.readouterr()
    assert err == ""

    # order of lines doesn't matter and is not guaranteed
    out_lines = out.splitlines()
    assert set(out_lines) == {f"Validated {file}" for file in unformatted_files}
