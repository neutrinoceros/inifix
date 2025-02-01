# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "packaging==24.2",
#     "tomli==2.2.1 ; python_version < '3.11'",
# ]
# ///
import re
import subprocess
import sys
from dataclasses import dataclass
from difflib import unified_diff
from pathlib import Path

from packaging.requirements import Requirement
from packaging.specifiers import Specifier
from packaging.version import Version

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

REV_REGEXP = re.compile(r"rev:\s+v.*")
STABLE_VER_REGEXP = re.compile(r"^\d+\.*\d+\.\d+$")
STABLE_TAG_REGEXP = re.compile(r"^v\d+\.*\d+\.\d+$")
ROOT = Path(__file__).parents[1]
LIB_DIR = ROOT / "lib" / "inifix"
README = LIB_DIR / "README.md"
CLI_PYPROJECT_TOML = ROOT / "pyproject.toml"
LIB_PYPROJECT_TOML = LIB_DIR / "pyproject.toml"


@dataclass(frozen=True)
class Metadata:
    current_lib_static_version: Version
    current_cli_requirement: Requirement
    lib_requires_python: Specifier
    cli_requires_python: Specifier
    latest_git_tag: str

    @property
    def latest_git_version(self) -> Version:
        if not STABLE_TAG_REGEXP.match(self.latest_git_tag):
            print(
                f"Failed to parse git tag (got {self.latest_git_tag})", file=sys.stderr
            )
            raise SystemExit(1)
        return Version(self.latest_git_tag)


def check_static_version(md: Metadata) -> int:
    if not STABLE_VER_REGEXP.match(str(md.current_lib_static_version)):
        print(
            f"Current static version {md.current_lib_static_version} doesn't "
            "conform to expected pattern for a stable sem-ver version.",
            file=sys.stderr,
        )
        return 1
    elif md.current_lib_static_version < md.latest_git_version:
        print(
            f"Current static version {md.current_lib_static_version} appears "
            f"to be older than latest git tag {md.latest_git_tag}",
            file=sys.stderr,
        )
        return 1
    else:
        print("Check static version: ok", file=sys.stderr)
        return 0


def check_inifix_cli_requirement(md: Metadata) -> int:
    if md.current_cli_requirement.specifier != f"=={md.current_lib_static_version}":
        print(
            f"inifix-cli is requiring inifix as {md.current_cli_requirement} "
            f"which is out of sync with inifix's version (expected =={md.current_lib_static_version})",
            file=sys.stderr,
        )
        return 1
    else:
        print("Check pinned version: ok", file=sys.stderr)
        return 0


def check_requires_python(md: Metadata) -> int:
    if md.cli_requires_python != md.lib_requires_python:
        print(
            f"inifix-cli's python requirement ({md.cli_requires_python}) "
            f"is out of sync with inifix's ({md.lib_requires_python})",
            file=sys.stderr,
        )
        return 1
    else:
        print("Check requires-python: ok")
        return 0


def check_readme(md: Metadata) -> int:
    text = README.read_text()
    if md.current_lib_static_version.is_devrelease:
        expected_tag = md.latest_git_tag
    else:
        expected_tag = f"v{md.current_lib_static_version}"
    if text != (expected := REV_REGEXP.sub(f"rev: {expected_tag}", text)):
        diff = "\n".join(
            line.removesuffix("\n")
            for line in unified_diff(
                text.splitlines(),
                expected.splitlines(),
                fromfile=str(LIB_PYPROJECT_TOML),
            )
        )
        print(diff, file=sys.stderr)
        return 1
    else:
        print("Check README.md: ok", file=sys.stderr)
        return 0


def main() -> int:
    with open(LIB_PYPROJECT_TOML, "rb") as fh:
        lib_table = tomllib.load(fh)
        current_lib_static_version = Version(lib_table["project"]["version"])
        current_lib_requires_python = Specifier(lib_table["project"]["requires-python"])
    with open(CLI_PYPROJECT_TOML, "rb") as fh:
        cli_table = tomllib.load(fh)
        current_cli_requires_python = Specifier(cli_table["project"]["requires-python"])
        cli_requirements = [
            Requirement(_) for _ in cli_table["project"]["dependencies"]
        ]
    for req in cli_requirements:
        if req.name == "inifix":
            current_cli_requirement = req
            break
    else:
        raise RuntimeError(f"failed to parse {CLI_PYPROJECT_TOML}")

    cp = subprocess.run(
        ["git", "describe", "--tags", "--abbrev=0"],
        check=True,
        capture_output=True,
    )
    cp_stdout = cp.stdout.decode().strip()

    md = Metadata(
        current_lib_static_version,
        current_cli_requirement,
        current_lib_requires_python,
        current_cli_requires_python,
        cp_stdout,
    )

    return (
        check_static_version(md)
        or check_inifix_cli_requirement(md)
        or check_requires_python(md)
        or check_readme(md)
    )


if __name__ == "__main__":
    raise SystemExit(main())
