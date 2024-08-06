import shutil
from pathlib import Path

import pytest

from inifix.format import main as inifix_format_cli

DATA_DIR = Path(__file__).parent / "data"


N_FILES = 257


@pytest.fixture
def unformated_files(tmp_path):
    in_file = DATA_DIR / "format-in.ini"
    files = []
    for file_no in range(N_FILES):
        new_file = tmp_path / f"{file_no}.ini"
        shutil.copy(in_file, new_file)
        files.append(new_file.resolve())

    yield files


def test_inifix_format_cli(unformated_files, capsys):
    ret = inifix_format_cli([str(f) for f in unformated_files])
    assert ret != 0

    out, err = capsys.readouterr()
    assert out == ""

    # order of lines doesn't matter and is not guaranteed
    err_lines = err.splitlines()
    assert set(err_lines) == {f"Fixing {file}" for file in unformated_files}

    expected = (DATA_DIR / "format-out.ini").read_text()
    for file in unformated_files:
        body = file.read_text()
        assert body == expected
