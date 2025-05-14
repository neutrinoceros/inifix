import os
import shutil
import textwrap
from difflib import unified_diff
from pathlib import Path
from stat import S_IREAD

import pytest
import typer.testing

import inifix
import inifix_cli
from inifix_cli import app

runner = typer.testing.CliRunner()
N_FILES = 257


@pytest.fixture
def unformatted_files(datadir_root, tmp_path):
    in_file = datadir_root / "format-in.ini"
    files = []
    for file_no in range(N_FILES):
        new_file = tmp_path / f"{file_no}.ini"
        shutil.copy(in_file, new_file)
        files.append(new_file.resolve())

    yield files


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


def wrap(t: str) -> str:
    return "\n".join(textwrap.wrap(t))


def assert_text_equal(actual: str, desired: str):
    assert wrap(actual) == wrap(desired)


def assert_text_includes(actual, desired):
    assert wrap(desired) in wrap(desired)


class TestValidate:
    def test_empty_file(self, tmp_path):
        target = tmp_path / "invalid_file"
        target.touch()
        result = runner.invoke(app, ["validate", str(target)])
        assert result.exit_code != 0
        assert_text_includes(result.stdout, f"Failed to validate {target}:")
        assert_text_includes(result.stdout, "appears to be empty.\n")

    def test_missing_file(self, tmp_path):
        target = tmp_path / "not_a_file"
        result = runner.invoke(app, ["validate", str(target)])
        assert result.exit_code != 0
        assert_text_includes(result.stdout, f"Error: could not find {target}")

    def test_invalid_files(self, invalid_file):
        result = runner.invoke(app, ["validate", str(invalid_file)])
        assert result.stdout.startswith("Failed to validate")
        assert result.exit_code != 0

    def test_valid_files(self, inifile_root):
        result = runner.invoke(app, ["validate", str(inifile_root)])

        assert result.stdout == f"Validated {inifile_root}\n"
        assert result.stderr == ""
        assert result.exit_code == 0

    def test_concurrency(self, unformatted_files, capsys):
        result = runner.invoke(app, ["validate", *(str(f) for f in unformatted_files)])
        assert result.exit_code == 0
        assert result.stderr == ""

        # order of lines doesn't matter and is not guaranteed
        out_lines = result.stdout.splitlines()
        assert set(out_lines) == {f"Validated {file}" for file in unformatted_files}


class TestFormat:
    @pytest.mark.parametrize("args", [(), ("--skip-validation",)])
    def test_format_keep_data(self, args, datadir_root, inifile_root, tmp_path):
        target = tmp_path / inifile_root.name

        ref_data = inifix.load(inifile_root)
        shutil.copyfile(inifile_root, target)

        result = runner.invoke(app, ["format", str(target), *args])
        assert isinstance(result.exit_code, int)

        data_new = inifix.load(target)
        assert data_new == ref_data

    @pytest.mark.parametrize(
        "infile, expect_diff",
        [("format-in.ini", True), ("format-out.ini", False)],
    )
    def test_exact_format_diff(self, datadir_root, infile, expect_diff):
        def diff_file(f1: Path, f2: Path) -> str:
            return (
                "\n".join(
                    line.removesuffix("\n")
                    for line in unified_diff(
                        f1.read_text().splitlines(),
                        f2.read_text().splitlines(),
                        fromfile=str(f1),
                    )
                )
                + "\n"
            )

        body = (datadir_root / infile).read_text()

        result = runner.invoke(app, ["format", str(datadir_root / infile), "--diff"])
        if expect_diff:
            assert result.exit_code != 0
            expected = diff_file(datadir_root / infile, datadir_root / "format-out.ini")
            assert result.stdout == expected
            assert result.stderr == ""
        else:
            assert result.exit_code == 0
            assert result.stdout == ""
            assert result.stderr == ""

        assert (datadir_root / infile).read_text() == body

    def test_exact_format_inplace(self, datadir_root, tmp_path):
        target = tmp_path / "result.stdout.ini"
        shutil.copyfile(datadir_root / "format-in.ini", target)

        result = runner.invoke(app, ["format", str(target)])
        assert result.exit_code != 0
        assert_text_equal(result.stdout, f"Fixing {target}")

        expected = (datadir_root / "format-out.ini").read_text()
        res = target.read_text()
        assert res == expected

    def test_no_parameters(self, tmp_path):
        target = tmp_path / "no_params.ini"
        target.write_text(
            "\n".join(
                [
                    "    # comment 1",
                    "[Section A]",
                    "  # comment 2",
                    " # comment 3",
                    "[Section B]",
                ]
            )
        )
        result = runner.invoke(app, ["format", str(target)])
        assert result.exit_code != 0

        expected = "\n".join(
            [
                "# comment 1",
                "",
                "[Section A]",
                "# comment 2",
                "# comment 3",
                "",
                "[Section B]\n",
            ]
        )
        assert target.read_text() == expected

    def test_missing_file(self, tmp_path):
        target = tmp_path / "not_a_file"
        result = runner.invoke(app, ["format", str(target)])
        assert result.exit_code != 0
        assert_text_equal(result.stdout, f"Error: could not find {target}")

    def test_empty_file(self, tmp_path):
        target = tmp_path / "invalid_file"
        target.touch()
        result = runner.invoke(app, ["format", str(target)])
        assert result.exit_code != 0
        assert_text_includes(
            result.stdout, f"Error: {str(target)!r} appears to be empty.\n"
        )

    def test_error_read_only_file(self, inifile_root, tmp_path):
        target = tmp_path / inifile_root.name
        shutil.copy(inifile_root, target)

        data = target.read_text()
        if inifix.format_string(data) == data:
            return

        os.chmod(target, S_IREAD)

        result = runner.invoke(app, ["format", str(target)])
        assert result.exit_code != 0
        assert_text_includes(
            result.stdout,
            f"Error: could not write to {target} (permission denied)\n",
        )

    def test_diff_stdout(self, inifile_root, tmp_path):
        target = tmp_path / inifile_root.name
        shutil.copy(inifile_root, target)

        result = runner.invoke(app, ["format", str(target), "--diff"])
        # we can't predict if formatting is needed
        assert isinstance(result.exit_code, int)

        if result.exit_code == 0:
            assert result.stdout == ""
        else:
            assert result.stdout != ""

    def test_report_noop(self, datadir_root, tmp_path):
        inifile_root = datadir_root / "format-out.ini"
        target = tmp_path / inifile_root.name

        shutil.copyfile(inifile_root, target)

        result = runner.invoke(app, ["format", str(target), "--report-noop"])
        assert result.exit_code == 0
        assert result.stdout == f"{target} is already formatted\n"

    def test_format_quoted_strings_with_whitespaces(self, tmp_path):
        target = tmp_path / "spaces.ini"

        inserted = '''Eggs 'Bacon Saussage'     "spam"'''
        expected = """Eggs    'Bacon Saussage'  "spam"\n"""
        target.write_text(inserted)
        result = runner.invoke(app, ["format", str(target)])
        assert result.exit_code != 0

        assert target.read_text() == expected

    def test_data_preservation(self, inifile_root, tmp_path):
        # check that perilous string manipulations do not destroy data
        initial_mapping = inifix.load(inifile_root)
        target = tmp_path / inifile_root.name
        shutil.copyfile(inifile_root, target)
        runner.invoke(app, ["format", str(target)])
        round_mapping = inifix.load(target)
        assert round_mapping == initial_mapping

    def test_single_core(self, monkeypatch, tmp_path):
        # regression test for gh-251
        target = tmp_path / "spaces.ini"

        inserted = '''Eggs 'Bacon Saussage'     "spam"'''
        target.write_text(inserted)

        monkeypatch.setattr(inifix_cli, "get_cpu_count", lambda: 1)
        runner.invoke(app, ["format", str(target)])

    def test_concurrency(self, datadir_root, unformatted_files):
        result = runner.invoke(app, ["format", *(str(f) for f in unformatted_files)])
        assert result.exit_code != 0

        # order of lines doesn't matter and is not guaranteed
        err_lines = result.stdout.splitlines()
        assert set(err_lines) == {f"Fixing {file}" for file in unformatted_files}

        expected = (datadir_root / "format-out.ini").read_text()
        for file in unformatted_files:
            body = file.read_text()
            assert body == expected
